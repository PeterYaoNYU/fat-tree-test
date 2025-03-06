# -*- coding: utf-8 -*-
"""fat tree for distributed sys"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

# Create a portal context and request object.
pc = portal.Context()
request = pc.makeRequestRSpec()

#
# 1) Define Nodes and Their Interfaces
#

# switch1 (RawPC)
node_switch1 = request.RawPC('switch1')
iface0 = node_switch1.addInterface('interface-0')  # on link-0
iface1 = node_switch1.addInterface('interface-3')  # on link-1

# node-0 (Xen VM)
node_0 = request.XenVM('node-0')
iface2 = node_0.addInterface('interface-1')        # on link-0

# node-1 (Xen VM)
node_1 = request.XenVM('node-1')
iface3 = node_1.addInterface('interface-2')        # on link-0

# switch2 (RawPC)
node_switch2 = request.RawPC('switch2')
iface4 = node_switch2.addInterface('interface-4')  # on link-1
iface5 = node_switch2.addInterface('interface-5')  # on link-2
iface6 = node_switch2.addInterface('interface-8')  # on link-3

# node-2 (Xen VM)
node_2 = request.XenVM('node-2')
iface7 = node_2.addInterface('interface-6')        # on link-2

# switch3 (RawPC)
node_switch3 = request.RawPC('switch3')
iface8 = node_switch3.addInterface('interface-7')  # on link-3
iface9 = node_switch3.addInterface('interface-10') # on link-4

# node-4 (Xen VM)
node_4 = request.XenVM('node-4')
iface10 = node_4.addInterface('interface-11')      # on link-4

# node-3 (Xen VM)
node_3 = request.XenVM('node-3')
iface11 = node_3.addInterface('interface-9')       # on link-4

#
# 2) Define Links (shared L2 segments)
#

# link-0: switch1, node-0, node-1 (three endpoints => /24)
link_0 = request.Link('link-0')
link_0.Site('undefined')
link_0.addInterface(iface0)
link_0.addInterface(iface2)
link_0.addInterface(iface3)

# link-1: switch1 <-> switch2 (/30)
link_1 = request.Link('link-1')
link_1.Site('undefined')
link_1.addInterface(iface1)
link_1.addInterface(iface4)

# link-2: switch2 <-> node-2 (/30)
link_2 = request.Link('link-2')
link_2.Site('undefined')
link_2.addInterface(iface5)
link_2.addInterface(iface7)

# link-3: switch2 <-> switch3 (/30)
link_3 = request.Link('link-3')
link_3.Site('undefined')
link_3.addInterface(iface8)
link_3.addInterface(iface6)

# link-4: switch3, node-3, node-4 (three endpoints => /24)
link_4 = request.Link('link-4')
link_4.Site('undefined')
link_4.addInterface(iface11)
link_4.addInterface(iface9)
link_4.addInterface(iface10)

#
# 3) Assign IP Addresses to Each Interface
#

# link-0 => 10.0.0.0/24
iface0.addAddress(pg.IPv4Address("10.0.0.1", "255.255.255.0"))  # switch1
iface2.addAddress(pg.IPv4Address("10.0.0.2", "255.255.255.0"))  # node-0
iface3.addAddress(pg.IPv4Address("10.0.0.3", "255.255.255.0"))  # node-1

# link-1 => 10.0.1.0/30
iface1.addAddress(pg.IPv4Address("10.0.1.1", "255.255.255.252")) # switch1
iface4.addAddress(pg.IPv4Address("10.0.1.2", "255.255.255.252")) # switch2

# link-2 => 10.0.2.0/30
iface5.addAddress(pg.IPv4Address("10.0.2.1", "255.255.255.252")) # switch2
iface7.addAddress(pg.IPv4Address("10.0.2.2", "255.255.255.252")) # node-2

# link-3 => 10.0.3.0/30
iface8.addAddress(pg.IPv4Address("10.0.3.1", "255.255.255.252")) # switch3
iface6.addAddress(pg.IPv4Address("10.0.3.2", "255.255.255.252")) # switch2

# link-4 => 10.0.4.0/24
iface11.addAddress(pg.IPv4Address("10.0.4.1", "255.255.255.0"))  # node-3
iface9.addAddress(pg.IPv4Address("10.0.4.2", "255.255.255.0"))   # switch3
iface10.addAddress(pg.IPv4Address("10.0.4.3", "255.255.255.0"))  # node-4

#
# 4) Add Routing Commands (Enable IP Forwarding + Static Routes)
#
#   - End-nodes (node-0..node-4) each get a default route to their local switch.
#   - Switches forward to each other’s subnets.
#

###################
# switch1 routing #
###################
node_switch1.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1

# We directly have:
#   10.0.0.0/24  on interface-0
#   10.0.1.0/30  on interface-3
# For subnets behind switch2 (10.0.2.0/30, 10.0.3.0/30, 10.0.4.0/24), route via 10.0.1.2
sudo ip route add 10.0.2.0/30 via 10.0.1.2
sudo ip route add 10.0.3.0/30 via 10.0.1.2
sudo ip route add 10.0.4.0/24 via 10.0.1.2
"""))

##################
# switch2 routing
##################
node_switch2.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1

# We directly have:
#   10.0.1.0/30  on interface-4
#   10.0.2.0/30  on interface-5
#   10.0.3.0/30  on interface-8
# For link-0 (10.0.0.0/24), go via switch1: 10.0.1.1
sudo ip route add 10.0.0.0/24 via 10.0.1.1
# For link-4 (10.0.4.0/24), go via switch3: 10.0.3.1
sudo ip route add 10.0.4.0/24 via 10.0.3.1
"""))

##################
# switch3 routing
##################
node_switch3.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1

# We directly have:
#   10.0.3.0/30 on interface-7
#   10.0.4.0/24 on interface-10
# For link-0, link-1, link-2 => route via switch2: 10.0.3.2
sudo ip route add 10.0.0.0/24 via 10.0.3.2
sudo ip route add 10.0.1.0/30 via 10.0.3.2
sudo ip route add 10.0.2.0/30 via 10.0.3.2
"""))

###############
# node-0 route
###############
node_0.addService(pg.Execute(shell="bash", command="""
# single interface at 10.0.0.2 -> default route via switch1 at 10.0.0.1
sudo ip route add default via 10.0.0.1
"""))

###############
# node-1 route
###############
node_1.addService(pg.Execute(shell="bash", command="""
sudo ip route add default via 10.0.0.1
"""))

###############
# node-2 route
###############
node_2.addService(pg.Execute(shell="bash", command="""
# single interface at 10.0.2.2 -> default route via 10.0.2.1
sudo ip route add default via 10.0.2.1
"""))

###############
# node-3 route
###############
node_3.addService(pg.Execute(shell="bash", command="""
# single interface at 10.0.4.1 -> default route via 10.0.4.2
sudo ip route add default via 10.0.4.2
"""))

###############
# node-4 route
###############
node_4.addService(pg.Execute(shell="bash", command="""
# single interface at 10.0.4.3 -> default route via 10.0.4.2
sudo ip route add default via 10.0.4.2
"""))

# Finally, print the RSpec
pc.printRequestRSpec(request)
