# -*- coding: utf-8 -*-
"""fat tree for distributed sys"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

pc = portal.Context()
request = pc.makeRequestRSpec()

# Define Nodes and Their Interfaces

node_switch1 = request.RawPC('switch1')
iface0 = node_switch1.addInterface('interface-0')  # on link-0
iface1 = node_switch1.addInterface('interface-3')  # on link-1

node_0 = request.XenVM('node-0')
iface2 = node_0.addInterface('interface-1')        # on link-0

node_1 = request.XenVM('node-1')
iface3 = node_1.addInterface('interface-2')        # on link-0

node_switch2 = request.RawPC('switch2')
iface4 = node_switch2.addInterface('interface-4')  # on link-1
iface5 = node_switch2.addInterface('interface-5')  # on link-2
iface6 = node_switch2.addInterface('interface-8')  # on link-3

node_2 = request.XenVM('node-2')
iface7 = node_2.addInterface('interface-6')        # on link-2

node_switch3 = request.RawPC('switch3')
iface8 = node_switch3.addInterface('interface-7')  # on link-3
iface9 = node_switch3.addInterface('interface-10') # on link-4

node_4 = request.XenVM('node-4')
iface10 = node_4.addInterface('interface-11')      # on link-4

node_3 = request.XenVM('node-3')
iface11 = node_3.addInterface('interface-9')       # on link-4

# Define Links (L2 segments)

link_0 = request.Link('link-0')
link_0.Site('undefined')
link_0.addInterface(iface0)
link_0.addInterface(iface2)
link_0.addInterface(iface3)

link_1 = request.Link('link-1')
link_1.Site('undefined')
link_1.addInterface(iface1)
link_1.addInterface(iface4)

link_2 = request.Link('link-2')
link_2.Site('undefined')
link_2.addInterface(iface5)
link_2.addInterface(iface7)

link_3 = request.Link('link-3')
link_3.Site('undefined')
link_3.addInterface(iface8)
link_3.addInterface(iface6)

link_4 = request.Link('link-4')
link_4.Site('undefined')
link_4.addInterface(iface11)
link_4.addInterface(iface9)
link_4.addInterface(iface10)

# Assign IP Addresses

# link-0: 10.0.0.0/24
iface0.addAddress(pg.IPv4Address("10.0.0.1", "255.255.255.0"))
iface2.addAddress(pg.IPv4Address("10.0.0.2", "255.255.255.0"))
iface3.addAddress(pg.IPv4Address("10.0.0.3", "255.255.255.0"))

# link-1: 10.0.1.0/30
iface1.addAddress(pg.IPv4Address("10.0.1.1", "255.255.255.252"))
iface4.addAddress(pg.IPv4Address("10.0.1.2", "255.255.255.252"))

# link-2: 10.0.2.0/30
iface5.addAddress(pg.IPv4Address("10.0.2.1", "255.255.255.252"))
iface7.addAddress(pg.IPv4Address("10.0.2.2", "255.255.255.252"))

# link-3: 10.0.3.0/30
iface8.addAddress(pg.IPv4Address("10.0.3.1", "255.255.255.252"))
iface6.addAddress(pg.IPv4Address("10.0.3.2", "255.255.255.252"))

# link-4: 10.0.4.0/24
iface11.addAddress(pg.IPv4Address("10.0.4.1", "255.255.255.0"))
iface9.addAddress(pg.IPv4Address("10.0.4.2", "255.255.255.0"))
iface10.addAddress(pg.IPv4Address("10.0.4.3", "255.255.255.0"))

# Add Routing Commands

node_switch1.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1
sudo ip route add 10.0.2.0/30 via 10.0.1.2
sudo ip route add 10.0.3.0/30 via 10.0.1.2
sudo ip route add 10.0.4.0/24 via 10.0.1.2
"""))

node_switch2.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1
sudo ip route add 10.0.0.0/24 via 10.0.1.1
sudo ip route add 10.0.4.0/24 via 10.0.3.1
"""))

node_switch3.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1
sudo ip route add 10.0.0.0/24 via 10.0.3.2
sudo ip route add 10.0.1.0/30 via 10.0.3.2
sudo ip route add 10.0.2.0/30 via 10.0.3.2
"""))

node_0.addService(pg.Execute(shell="bash", command="""
sudo ip route add default via 10.0.0.1
"""))

node_1.addService(pg.Execute(shell="bash", command="""
sudo ip route add default via 10.0.0.1
"""))

node_2.addService(pg.Execute(shell="bash", command="""
sudo ip route add default via 10.0.2.1
"""))

node_3.addService(pg.Execute(shell="bash", command="""
sudo ip route add default via 10.0.4.2
"""))

node_4.addService(pg.Execute(shell="bash", command="""
sudo ip route add default via 10.0.4.2
"""))

pc.printRequestRSpec(request)
