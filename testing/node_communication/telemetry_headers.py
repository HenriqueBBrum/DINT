# Telemtry headers used inside p4 files


from scapy.all import *

TYPE_Telemetry = 0X6666

# Telemetry header containing general information
class Telemetry(Packet):
   name = "Telemetry"
   fields_desc = [ ByteField("hop_cnt", 0),
                     ByteField("telemetry_data_sz", 0),
                     BitField("next_header_type", 0, 16),
                     IntField("flow_id", 0)]
                     
# Telemetry header added to a packet by each switch
class Telemetry_Data(Packet):
   name = "Telemetry_Data"
   fields_desc = [ BitField("bos", 0, 1),
                   BitField("switch_id", 0, 7),
                   IntField("amt_bytes", 0),
                   BitField("prev_timestamp", 0, 48),
                   BitField("curr_timestamp", 0, 48)]


bind_layers(Ether, Telemetry, type=TYPE_Telemetry)
bind_layers(Telemetry, IP, hop_cnt=0)
bind_layers(Telemetry, Telemetry_Data)
bind_layers(Telemetry_Data, Telemetry_Data, bos=0)
bind_layers(Telemetry_Data, IP, bos=1)
