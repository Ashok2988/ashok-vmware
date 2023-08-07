"""
Author: ashokb@vmware.com
"""
import time
import requests
import json
import argparse
import getpass
requests.packages.urllib3.disable_warnings()

class EcMove(object):
 def __init__(self,nm,nu,np,ecid):
    self.nm=nm
    self.nu=nu
    self.np=np
    self.auth = (nu, np) 
    self.headers={'content-type': 'application/json'} 
    self.ecid=ecid
    self.ver=False
    self.authenticate()
    
 def authenticate(self):
   url="https://%s/api/v1/transport-zones" % (self.nm)
   resp=requests.get(url, auth=self.auth, headers=self.headers, verify=False)
   if not resp.ok:
      print("Auth failed, Please check creds")
   else:
      self.ver=True
      
 def _update_edge_clust(self,l):
    tier=[]
    
    for s in l:
      for i in s.split(' '):
        if  '/policy/api/v1/infra/tier-1s/' in i:
            for j in i.split('/'):
               if j.startswith('t1'):
                  tier.append(j)
    for tier1 in tier:
       url = "https://%s/policy/api/v1/infra/tier-1s/%s/locale-services" % (self.nm, tier1)
       resp=requests.get(url, auth=self.auth, headers=self.headers, verify=False)
       payload=json.loads(resp.content)
       path=payload['results'][0]['edge_cluster_path'].split('/')
       path[-1]=self.ecid
       newpayload={}
       newpayload['edge_cluster_path']='/'.join(path)
       url = "https://%s/policy/api/v1/infra/tier-1s/%s/locale-services/default" % (self.nm, tier1)
       resp = requests.patch(url, auth=self.auth, headers=self.headers, data=json.dumps(newpayload), verify=False)
       if resp.ok:
           print("Updated edge cluster for T1: %s" % tier1)
       else:
           print("Edge cluster update failed for T1: %s" % tier1)

def follow(file, sleep_sec=0.1):
    line = ''
    file.seek(0,2)
    while True:
        tmp = file.readline()
        if tmp is not None:
            line += tmp
            if line.endswith("\n"):
                yield line
                line = ''
        elif sleep_sec:
            time.sleep(sleep_sec)

def get_parse_arguments():
    parser = argparse.ArgumentParser(description='T1 EC update script') 
    parser.add_argument('--nsxip',
                        help='nsx manager ip',
                        required=True, default=False)
    parser.add_argument('--nsxuser',
                        help='nsx username',
                        required=True, default=False)
    parser.add_argument('--nsxpwd',
                        help='nsx password',
                         default=False)
    parser.add_argument('--ecid',
                        help='edge cluster id',
                        required=True, default=False)
    parser.add_argument('--t1c',
                        help='number of T1s to migrate',
                        required=True, default=False)
    return parser.parse_args()


if __name__ == '__main__':
    args=get_parse_arguments()
    if not args.nsxpwd:
       nsxpwd = getpass.getpass("NSX Manager password: ")    
    else:
       nsxpwd=args.nsxpwd
    nm = args.nsxip
    nu = args.nsxuser
    np = nsxpwd
    ecid = args.ecid
    t1c = int(args.t1c)
    obj=EcMove(nm,nu,np,ecid)
    if  obj.ver:
       
      with open("/var/log/policy/localhost_access_log.txt", 'r') as file:
        l=[]
        word=['t1','locale-services']
        for line in follow(file):
            if all(x in line for x in word) and 'virtual' not in line: 
               l.append(line)
      #the idea here is to move atleast half of the T1's to the second edge cluster, if customer has 400+ T1's we will pass t1c count as 200
      #so that half of the T1's move to second EC and remaining will stay on default cluster. wouldnt pose any capacity issues.
               if len(l)==t1c:
                  obj._update_edge_clust(l)
                  break
