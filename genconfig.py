#!/usr/bin/python

import argparse
import os
import yaml
import re

def gen_targets(servers, cluster):
    if ':' not in servers:
        raise Exception('Server list must contain a dc name')
    dcs = servers.split(':')
    res = {"labels": {"cluster": cluster, "dc": dcs[0]}}
    res["targets"] = dcs[1].split(',')
    return res;

def get_servers_from_nodetool_status(filename):
    res = []
    dc = None
    ips = []
    with open(filename, 'r') as status_file:
        for l in status_file.readlines():
            if dc:
                ip = re.search(r"..  ([\d\.]+)\s", l)
                if ip:
                    ips.append(ip.group(1))
            m = re.search(r"Datacenter: (.*)$", l)
            if m:
                if dc:
                    res.append(dc + ":" + ",".join(ips))
                ips = []
                dc = m.group(1)
    if dc:
        res.append(dc + ":" + ",".join(ips))
    return res

def dump_yaml_no_dc(directory, filename, servers):
    try:
        os.mkdir(directory)
    except OSError, err:
        if err.errno != 17:
            raise
        pass
    stream = file(os.path.join(directory, filename), 'w')
    yaml.dump([{"targets": servers}], stream, default_flow_style=False)

def dump_yaml(directory, filename, servers, cluster):
    try:
        os.mkdir(directory)
    except OSError, err:
        if err.errno != 17:
            raise
        pass
    with open(os.path.join(directory, filename), 'w') as yml_file:
        yaml.dump([gen_targets(s, cluster) for s in servers], yml_file, default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate configuration for prometheus")
    parser.add_argument('-d', '--directory', help="directory where to generate the configuration files", type=str, default="./")
    parser.add_argument('-s', '--scylla', help="Deprecated: Generate scylla_servers.yml file", action='store_true')
    parser.add_argument('-n', '--node', help="Deprecated: Generate node_exporter_servers.yml file", action='store_true')
    parser.add_argument('-c', '--cluster', help="The cluster name", type=str, default="my-cluster")
    parser.add_argument('-NS', '--nodetool-status', help="A file containing nodetool status", type=str)
    parser.add_argument('servers', help="list of nodes to configure, separated by space", nargs='*', type=str, metavar='node_ip')
    parser.add_argument('-dc', '--datacenters', action='append', help="list of dc and nodes to configure separated by space. Each dc/node entry is a combination of {dc}:ip1,ip2..ipn")
    arguments = parser.parse_args()

    if arguments.nodetool_status:
        dump_yaml(arguments.directory, 'scylla_servers.yml', get_servers_from_nodetool_status(arguments.nodetool_status), arguments.cluster)
    else:
        if arguments.servers:
            dump_yaml_no_dc(arguments.directory, 'scylla_servers.yml', arguments.servers)
        else:
            dump_yaml(arguments.directory, 'scylla_servers.yml', arguments.datacenters , arguments.cluster)
    if arguments.node:
        dump_yaml_no_dc(arguments.directory, 'node_exporter_servers.yml', arguments.servers)
