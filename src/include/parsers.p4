/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    // Parse ethernet, go to the Telemetry parser or IPv4 parser
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type) {
            TYPE_TELEMETRY: parse_telemetry;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    // Parse general information header based on hop_count. O means no tel_Data headers
    state parse_telemetry {
        packet.extract(hdr.telemetry);
        transition select(hdr.telemetry.hop_cnt) {
            0: parse_ipv4;
            default: parse_tel_data;
        }
    }

    // Parse tel_data header stack. Keep extracting headers until the one at the bottom of stack (bos). After extracting all tel_data headers, parse IPv4 header
    state parse_tel_data {
        packet.extract(hdr.tel_data.next);
        transition select(hdr.tel_data.last.bos) {
            1: parse_ipv4;
            default: parse_tel_data;
        }
    }

    // Parse IPv4 header. If there is a udp header, go to its parser
    state parse_ipv4{
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_UDP: parse_udp;
            default: accept;
        }
    }

    // Parse UDP header and exit parsing stage
    state parse_udp{
        packet.extract(hdr.udp);
        transition accept;
    }

}




/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr){
    apply {
        // Emit all valid headers with the order inside 'hdr' 
        packet.emit(hdr);
    }
}
