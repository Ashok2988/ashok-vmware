from pyVmomi import vim
from pyVim.connect import SmartConnectNoSSL, Disconnect
from collections import defaultdict
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter_client import Network
from com.vmware.vcenter.vm.hardware_client import Ethernet
from samples.vsphere.vcenter.helper import network_helper
from threading import Thread
from samples.vsphere.common import vapiconnect
import urllib3
import ipaddress
import time
import base64
import requests
import subprocess
import json


def get_session():
    auth_string = "administrator@vsphere.local:Vmware123!"
    auth_bytes = auth_string.encode()
    base64_byte = base64.b64encode(auth_bytes)
    l=str(base64_byte).strip('b').replace('=','')
    l=l.strip("'")
    response=requests.post('https://ashok-vcf-compute-vc.cptroot.com/api/session',verify=False, headers={"Authorization": "Basic %s" %l})
    return response.text

urllib3.disable_warnings()
import argparse


def subnet(cidr):
    li=[str(ip) for ip in ipaddress.IPv4Network(cidr)]
    mask=str(ipaddress.IPv4Network(cidr).netmask)
    li.pop()
    return li,mask
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
    parser.add_argument('--tempname',
                        help='template name',
                        required=True, default=False),

    parser.add_argument('--cidr',
                        help='cidr',
                        required=True, default=False),
    parser.add_argument('--network',
                        help='network',
                        required=True, default=False),
    parser.add_argument('--vms',
                        help='vm count',
                        required=True, default=False),
    parser.add_argument('--gw',
                        help='gw',
                        required=True, default=False)

    args=parser.parse_args()
    si = SmartConnectNoSSL(host=args.vcip, user=args.vcuser, pwd=args.vcpwd)
    with requests.session() as session:
        session.verify = False
        client = create_vsphere_client(server=args.vcip,
                                        username=args.vcuser,
                                        password=args.vcpwd,
                                        session=session)
        root_folder = si.content.rootFolder
        content = si.RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        template = None
        for vm in datacenter.vmFolder.childEntity:
             if vm.name == args.tempname:
                template = vm
                break
        for net in root_folder.childEntity[0].network:
               if net.name == args.network:
                   nn=net
                   break
        if template is None:
           raise Exception(f"Template '{template_name}' not found.")
        cluster = 'cluster2'
        for cluster_obj in datacenter.hostFolder.childEntity:
           if isinstance(cluster_obj, vim.ClusterComputeResource) and cluster_obj.name == cluster:
              cluster = cluster_obj
              break

        if cluster is None:
           raise Exception(f"Cluster '{cluster_name}' not found.")
        sub,mask=subnet(args.cidr)
        datastores = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True).view
        for ds in datastores:
              if ds.name=='vsanDatastore':
                 datastore=ds
                 break
        for i in range(int(args.vms)):
           deploy_spec = vim.vm.ConfigSpec()
           deploy_spec.numCPUs = 1
           deploy_spec.memoryMB = 1024
           network_spec = vim.vm.device.VirtualDeviceSpec()
           #network_spec.operation=vim.vm.device.VirtualDeviceSpec.Operation.edit
           network_spec.device = vim.vm.device.VirtualVmxnet3()
           network_spec.device.deviceInfo = vim.Description()
           network_spec.device.deviceInfo.label = 'Network Adapter 1'

           adapter_map = vim.vm.customization.AdapterMapping()
           adapter_map.adapter = vim.vm.customization.IPSettings()
           adapter_map.adapter.ip = vim.vm.customization.FixedIp()
           ipa=sub.pop()
           hname=ipa.split('.')

           adapter_map.adapter.ip.ipAddress = ipa
           adapter_map.adapter.subnetMask = mask
           adapter_map.adapter.gateway = args.gw
           adapter_map.adapter.dnsDomain = 'cptroot.com'
           adapter_map.adapter.dnsServerList = '10.172.106.1'

           global_ip_settings = vim.vm.customization.GlobalIPSettings()
           global_ip_settings.dnsServerList = ['10.172.106.1']

           customization_spec = vim.vm.customization.Specification()
           customization_spec.nicSettingMap = [adapter_map]
           ident=vim.vm.customization.LinuxPrep(domain='cptroot.com',
           hostName=vim.vm.customization.FixedName(
           name='n'+str(hname[-2])+str(hname[-1])))
           customization_spec.identity=ident
           customization_spec.globalIPSettings=global_ip_settings
           network_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
           network_spec.device.backing.network = nn
           network_spec.device.backing.deviceName = nn.name
           network_spec.device.backing.useAutoDetect = True
           network_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
           network_spec.device.connectable.startConnected = True
           network_spec.device.connectable.allowGuestControl = True


           deploy_spec.deviceChange = [network_spec]

           relospec = vim.vm.RelocateSpec()
           relospec.pool = cluster.resourcePool
           relospec.datastore=datastore
           task = template.Clone(name='-'.join(hname),folder=template.parent,  spec=vim.vm.CloneSpec(config=deploy_spec, location=relospec, customization=customization_spec ))

           while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
              pass

           if task.info.state == vim.TaskInfo.State.error:
              raise Exception(f"Deploy task failed: {task.info.error}")
           o=task.info.result._moId
           nic=(client.vcenter.vm.hardware.Ethernet.list(vm=o))[0]
           nic_update_spec = Ethernet.UpdateSpec(
                                        backing=Ethernet.BackingSpec(
                                        type=Ethernet.BackingType.DISTRIBUTED_PORTGROUP,
                                        network=nn._moId))
           client.vcenter.vm.hardware.Ethernet.update(o,'4000',nic_update_spec)
           task.info.result.PowerOnVM_Task()

        Disconnect(si)


if __name__ == '__main__':
    main()
