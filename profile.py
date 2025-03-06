# -*- coding: utf-8 -*-
"""Fat tree for distributed systems - revised for elect testing

   This version respects the original interface assignments:
     - Nodes 0 and 1 attach to switch1 via link-0.
     - Nodes 3 and 4 attach to switch3 via link-1.
     - Node2 attaches via a single interface.
     - switch2 has exactly 2 interfaces.
     
   To force data-center-style routing (e.g. traffic from switch3's spine toward
   node2 goes via switch2), we assign IP addresses on link-2 using a /29.
   On link-2, node2 and switch2 get the primary IPs while switch3 also gets an IP.
   Then, on switch3 we delete the automatically installed connected route for link-2
   and add a static route for 10.0.2.0/29 via switch2.
"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

pc = portal.Context()
request = pc.makeRequestRSpec()

# --- Define Nodes and Their Interfaces ---
# Node node-0
node_0 = request.XenVM('node-0')
iface0 = node_0.addInterface('interface-1')

# Node node-1
node_1 = request.XenVM('node-1')
iface1 = node_1.addInterface('interface-2')

# Node node-2 (will have only one interface)
node_2 = request.XenVM('node-2')
iface2 = node_2.addInterface('interface-6')

# Node node-3
node_3 = request.XenVM('node-3')
iface3 = node_3.addInterface('interface-4')

# Node node-4
node_4 = request.XenVM('node-4')
iface4 = node_4.addInterface('interface-5')

# Node switch1
node_switch1 = request.RawPC('switch1')
iface5 = node_switch1.addInterface('interface-0')
iface6 = node_switch1.addInterface('interface-10')

# Node switch2 (must have only 2 interfaces)
node_switch2 = request.RawPC('switch2')
iface7 = node_switch2.addInterface('interface-7')
iface8 = node_switch2.addInterface('interface-9')

# Node switch3
node_switch3 = request.RawPC('switch3')
iface9 = node_switch3.addInterface('interface-3')
iface10 = node_switch3.addInterface('interface-8')

# --- Define Links (L2 segments) ---
#
# link-0: Connects switch1, node-0, and node-1.
link_0 = request.Link('link-0')
link_0.Site('undefined')
link_0.addInterface(iface5)
link_0.addInterface(iface0)
link_0.addInterface(iface1)

# link-1: Connects switch3, node-3, and node-4.
link_1 = request.Link('link-1')
link_1.Site('undefined')
link_1.addInterface(iface9)
link_1.addInterface(iface3)
link_1.addInterface(iface4)

# link-2: Intended to carry traffic between node-2 and switch2.
# Although switch3's iface10 is physically on this link (to "reflect" the spine),
# CloudLab requires an IP on every member. Therefore, we assign all members an IP
# in a /29. Later, we force switch3 to use switch2 to reach node-2.
link_2 = request.Link('link-2')
link_2.Site('undefined')
link_2.addInterface(iface2)
link_2.addInterface(iface7)
link_2.addInterface(iface10)  # Now we assign an IP below

# link-3: Connects switch2 and switch1.
link_3 = request.Link('link-3')
link_3.Site('undefined')
link_3.addInterface(iface8)
link_3.addInterface(iface6)

# --- Assign IP Addresses ---
#
# For link-0 (10.0.0.0/24)
iface5.addAddress(pg.IPv4Address("10.0.0.1", "255.255.255.0"))
iface0.addAddress(pg.IPv4Address("10.0.0.2", "255.255.255.0"))
iface1.addAddress(pg.IPv4Address("10.0.0.3", "255.255.255.0"))

# For link-1 (10.0.1.0/24)
iface9.addAddress(pg.IPv4Address("10.0.1.1", "255.255.255.0"))
iface3.addAddress(pg.IPv4Address("10.0.1.2", "255.255.255.0"))
iface4.addAddress(pg.IPv4Address("10.0.1.3", "255.255.255.0"))

# For link-2, use 10.0.2.0/29.
# We assign:
#   - switch2 (iface7): 10.0.2.1/29
#   - node-2 (iface2): 10.0.2.2/29
#   - switch3 (iface10): 10.0.2.3/29
iface7.addAddress(pg.IPv4Address("10.0.2.1", "255.255.255.248"))
iface2.addAddress(pg.IPv4Address("10.0.2.2", "255.255.255.248"))
iface10.addAddress(pg.IPv4Address("10.0.2.3", "255.255.255.248"))

# For link-3 (10.0.3.0/24)
iface8.addAddress(pg.IPv4Address("10.0.3.1", "255.255.255.0"))
iface6.addAddress(pg.IPv4Address("10.0.3.2", "255.255.255.0"))

# --- Add Routing Commands ---
#
# Enable IP forwarding on the switches.
node_switch1.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1
"""))
node_switch2.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1
"""))
node_switch3.addService(pg.Execute(shell="bash", command="""
sudo sysctl -w net.ipv4.ip_forward=1
"""))

# Set default gateways for the VMs.
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
sudo ip route add default via 10.0.1.1
"""))
node_4.addService(pg.Execute(shell="bash", command="""
sudo ip route add default via 10.0.1.1
"""))

#
# The following static routes "force" inter-switch traffic so that:
#  - Traffic toward node-2 (10.0.2.0/29) from switch3 is sent via switch2.
#  - Other inter-leaf routes are similarly enforced.
#
# On switch1 (leaf)
node_switch1.addService(pg.Execute(shell="bash", command="""
# To reach node-2's network (10.0.2.0/29) via switch2 reachable on link-3:
sudo ip route add 10.0.2.0/29 via 10.0.3.1
sudo ip route add 10.0.1.0/24 via 10.0.3.1
"""))

# On switch2 (middle leaf)
node_switch2.addService(pg.Execute(shell="bash", command="""
# Route to nodes on switch1 (10.0.0.0/24) via switch1 on link-3:
sudo ip route add 10.0.0.0/24 via 10.0.3.2
sudo ip route add 10.0.1.0/24 via 10.0.2.3
"""))

# On switch3 (spine)
node_switch3.addService(pg.Execute(shell="bash", command="""
# Delete the automatically installed connected route for link-2.
# (Assuming the OS interface name for iface10 is 'interface-8'; adjust if needed.)
# sudo ip route del 10.0.2.0/29 dev interface-8
# Now, add a static route for node-2's network via switch2 (10.0.2.1):
sudo ip route add 10.0.2.0/29 via 10.0.2.1
# Also, route traffic destined for switch1's network via switch1 (reachable via link-3 through switch2):
sudo ip route add 10.0.0.0/24 via 10.0.2.1
"""))

# Print the generated rspec.
pc.printRequestRSpec(request)
