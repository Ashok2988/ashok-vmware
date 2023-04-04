from pyVmomi import vim
from pyVim.connect import SmartConnectNoSSL, Disconnect
from collections import defaultdict
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter_client import Network
from com.vmware.vcenter.vm.hardware_client import Ethernet
from samples.vsphere.vcenter.helper import network_helper
from threading import Thread
import urllib3

urllib3.disable_warnings()
import argparse
import requests


def parallel_exec(nothreads,vm_dict,dnet,creds):
        threads=[]
        vms=list(vm_dict.keys())
        for i in range(nothreads):
            vml=vms[i::nothreads]
            if len(vml)>0:

                tdict={x:vm_dict[x] for x in vml}
                t = Thread(target=execute, args=(tdict,dnet,creds))
                threads.append(t)

            else:
                break
        return threads

def execute(tdict,dnet,creds):
    session = requests.session()
    session.verify = False

    client = create_vsphere_client(server=creds['vc'],
                                        username=creds['user'],
                                        password=creds['pwd'],
                                        session=session)
    for vm in tdict:
        print("updating vm net for  %s to %s" %(vm,dnet))
        client.vcenter.vm.hardware.Ethernet.update(vm,tdict[vm]["nic_summary"],tdict[vm]["nic_update_spec"])

def main():

    parser = argparse.ArgumentParser(description='Network reconfigure script')
    parser.add_argument('--vcip',
                        help='vcenter ip',
                        required=True, default=False)
    parser.add_argument('--vcuser',
                        help='vcenter username',
                        required=True, default=False)
    parser.add_argument('--vcpwd',
                        help='vcenter password',
                         default=False)
    parser.add_argument('--srcnet',
                        help='src network name',
                        required=True, default=False)
    parser.add_argument('--dstnet',
                        help='dst network name',
                        required=True, default=False)
    args=parser.parse_args()
    si = SmartConnectNoSSL(host=args.vcip, user=args.vcuser, pwd=args.vcpwd)
    session = requests.session()
    session.verify = False


    client = create_vsphere_client(server=args.vcip,
                                        username=args.vcuser,
                                        password=args.vcpwd,
                                        session=session)
    root_folder = si.content.rootFolder
    network_name = args.srcnet
    tnetwork_name = args.dstnet

    network = defaultdict(list)
    dvhsmap=defaultdict(set)
    dvhtmap=defaultdict(set)

    tnetwork_map=defaultdict(list)
    for net in root_folder.childEntity[0].network:
        if net.name == network_name:
            nname=net._GetMoId()
            for i in net.host:
                dvhsmap[nname].add(i._GetMoId())
            for vm in net.vm:
                vm=vm._GetMoId()
                network[nname].append(vm)
        elif net.name == tnetwork_name:
            nname=net._GetMoId()
            for i in net.host:
                dvhtmap[nname].add(i._GetMoId())



    res={}
    for k,v in network.items():
        for vm in v:
            nic_summaries = client.vcenter.vm.hardware.Ethernet.list(vm=vm)
            for nic_summary in nic_summaries:
                back=client.vcenter.vm.hardware.Ethernet.get(vm=vm,nic=nic_summary.nic).backing.network
                if back in network.keys():
                    for i in dvhtmap.keys():
                        if dvhtmap[i]==dvhsmap[back]:
                            distributed_network=i
                            break
                    nic_update_spec = Ethernet.UpdateSpec(
                                    backing=Ethernet.BackingSpec(
                                    type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
                                    network=distributed_network))
                    res[vm]={"nic_summary":nic_summary.nic,"nic_update_spec":nic_update_spec}
                    break

    inp = ''
    creds={'vc':args.vcip,'user': args.vcuser,'pwd': args.vcpwd }
    threads=parallel_exec(20,res,args.dstnet,creds)
    while inp!='yes':
        inp = input("pls type 'yes' if gw migration is done:")
    if inp=='yes':
         [thread.start() for thread in threads]
         [thread.join() for thread in threads]


    Disconnect(si)


if __name__ == '__main__':
    main()
