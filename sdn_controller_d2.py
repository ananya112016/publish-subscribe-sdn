
import os
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib.packet import packet, ethernet, ether_types
from os_ken.lib import hub


class SDNControllerD2(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    POLICY_COOKIE = 0xD200

    def __init__(self, *args, **kwargs):
        super(SDNControllerD2, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.policy_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "d2_policy.txt"
        )
        self.current_policy = None
        self.monitor = hub.spawn(self.policy_loop)

    def add_flow(self, dp, priority, match, actions, cookie=0):
        parser = dp.ofproto_parser
        instructions = [
            parser.OFPInstructionActions(
                dp.ofproto.OFPIT_APPLY_ACTIONS, actions
            )
        ]
        dp.send_msg(parser.OFPFlowMod(
            datapath=dp,
            cookie=cookie,
            priority=priority,
            match=match,
            instructions=instructions
        ))

    def apply_policy(self, dp, policy):
        parser = dp.ofproto_parser
        ofp = dp.ofproto

        if policy == "BLOCK":
            # Block client-to-broker TCP traffic.
            match1 = parser.OFPMatch(
                eth_type=0x0800,
                ipv4_dst="10.0.0.1",
                ip_proto=6,
                tcp_dst=5000
            )
            dp.send_msg(parser.OFPFlowMod(
                datapath=dp,
                cookie=self.POLICY_COOKIE,
                priority=200,
                match=match1,
                instructions=[]
            ))

            # Block broker-to-client TCP traffic.
            match2 = parser.OFPMatch(
                eth_type=0x0800,
                ipv4_src="10.0.0.1",
                ip_proto=6,
                tcp_src=5000
            )
            dp.send_msg(parser.OFPFlowMod(
                datapath=dp,
                cookie=self.POLICY_COOKIE,
                priority=200,
                match=match2,
                instructions=[]
            ))

            self.logger.info("D2 POLICY: BROKER TRAFFIC BLOCKED")

        elif policy == "ALLOW":
            dp.send_msg(parser.OFPFlowMod(
                datapath=dp,
                cookie=self.POLICY_COOKIE,
                cookie_mask=0xffffffffffffffff,
                command=ofp.OFPFC_DELETE,
                out_port=ofp.OFPP_ANY,
                out_group=ofp.OFPG_ANY,
                match=parser.OFPMatch()
            ))

            self.logger.info("D2 POLICY: BROKER TRAFFIC ALLOWED")

    def policy_loop(self):
        while True:
            try:
                with open(self.policy_file, "r") as f:
                    policy = f.read().strip().upper()

                if policy not in ("ALLOW", "BLOCK"):
                    hub.sleep(1)
                    continue

                if policy != self.current_policy:
                    for dp in list(self.datapaths.values()):
                        self.apply_policy(dp, policy)
                    self.current_policy = policy

            except FileNotFoundError:
                pass
            except Exception as error:
                self.logger.error("Policy update error: %s", error)

            hub.sleep(1)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features(self, ev):
        dp = ev.msg.datapath
        self.datapaths[dp.id] = dp
        parser = dp.ofproto_parser
        ofp = dp.ofproto

        # Forward publisher/subscriber traffic to broker.
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst="10.0.0.1",
            ip_proto=6,
            tcp_dst=5000
        )
        self.add_flow(dp, 100, match, [parser.OFPActionOutput(1)])

        # Forward broker replies to clients.
        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src="10.0.0.1",
            ip_proto=6,
            tcp_src=5000
        )
        self.add_flow(dp, 100, match, [parser.OFPActionOutput(2)])

        # Send unmatched packets to controller.
        self.add_flow(
            dp, 0, parser.OFPMatch(),
            [parser.OFPActionOutput(
                ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER
            )]
        )

        # Apply the current policy to a newly connected switch.
        try:
            with open(self.policy_file, "r") as f:
                policy = f.read().strip().upper()
            if policy in ("ALLOW", "BLOCK"):
                self.apply_policy(dp, policy)
        except FileNotFoundError:
            pass

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in(self, ev):
        msg = ev.msg
        dp = msg.datapath
        parser = dp.ofproto_parser
        ofp = dp.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None or eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        in_port = msg.match["in_port"]
        self.mac_to_port.setdefault(dp.id, {})
        self.mac_to_port[dp.id][eth.src] = in_port

        out_port = self.mac_to_port[dp.id].get(
            eth.dst, ofp.OFPP_FLOOD
        )
        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD:
            match = parser.OFPMatch(
                in_port=in_port,
                eth_dst=eth.dst
            )
            self.add_flow(dp, 1, match, actions)

        dp.send_msg(parser.OFPPacketOut(
            datapath=dp,
            buffer_id=ofp.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=msg.data
        ))
