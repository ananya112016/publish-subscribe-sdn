
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib.packet import packet, ethernet, ether_types

class SDNController(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SDNController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def add_flow(self, dp, priority, match, actions):
        parser = dp.ofproto_parser
        instructions = [
            parser.OFPInstructionActions(
                dp.ofproto.OFPIT_APPLY_ACTIONS, actions
            )
        ]
        dp.send_msg(
            parser.OFPFlowMod(
                datapath=dp,
                priority=priority,
                match=match,
                instructions=instructions
            )
        )

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features(self, ev):
        dp = ev.msg.datapath
        parser = dp.ofproto_parser
        ofp = dp.ofproto

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst="10.0.0.1",
            ip_proto=6,
            tcp_dst=5000
        )
        self.add_flow(
            dp, 100, match,
            [parser.OFPActionOutput(1)]
        )

        match = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_src="10.0.0.1",
            ip_proto=6,
            tcp_src=5000
        )
        self.add_flow(
            dp, 100, match,
            [parser.OFPActionOutput(2)]
        )

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(
                ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER
            )
        ]
        self.add_flow(dp, 0, match, actions)

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
        dpid = dp.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][eth.src] = in_port

        out_port = self.mac_to_port[dpid].get(
            eth.dst, ofp.OFPP_FLOOD
        )
        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD:
            match = parser.OFPMatch(
                in_port=in_port,
                eth_dst=eth.dst
            )
            self.add_flow(dp, 1, match, actions)

        dp.send_msg(
            parser.OFPPacketOut(
                datapath=dp,
                buffer_id=ofp.OFP_NO_BUFFER,
                in_port=in_port,
                actions=actions,
                data=msg.data
            )
        )

