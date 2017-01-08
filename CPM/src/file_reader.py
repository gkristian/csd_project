#f = open("cpm_tester_weights_feeder.txt","r")
#data =
filename_containing_nfm_metrics = "cpm_tester_weights_feeder.txt"
with open(filename_containing_nfm_metrics,"r") as f:
    for line in f:
        line = line.strip() #remove space from start and end of line
        #ignore lines i n file beginning with a # continue. I could have also used a pattern matcher '^#' but that would have been expensive
        if not line or line[0] == '#':
            continue

        src_node_to_dst_node,nfm_values = line.split(':')
        link_util, packet_drops = nfm_values.split(',')
        print "node =",src_node_to_dst_node
        print "link_util", link_util
        print "packet_drops",packet_drops
