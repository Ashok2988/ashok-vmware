import time
import requests
import json
import argparse
import getpass
from threading import Thread
requests.packages.urllib3.disable_warnings()

class EcMove(object):
 def __init__(self,nm,nu,np):
    self.nm=nm
    self.nu=nu
    self.np=np
    self.auth = (nu, np)
    self.headers={'content-type': 'application/json'}
#    self.ecid=ecid
    self.ver=False
    self.authenticate()

 def authenticate(self):
   url="https://%s/api/v1/transport-zones" % (self.nm)
   resp=requests.get(url, auth=self.auth, headers=self.headers, verify=False)
   if not resp.ok:
      print("Auth failed, Please check creds")
   else:
      self.ver=True

 def _update_edge_clust(self,l,ecid):
    ec=ecid
    tier=[]

    for s in l:
      for i in s.split(' '):
        if  '/policy/api/v1/infra/tier-1s/' in i:
            for j in i.split('/'):
               if j.startswith('t1'):
                  tier.append(j)
    #print(tier)
    for tier1 in tier:
       url = "https://%s/policy/api/v1/infra/tier-1s/%s/locale-services" % (self.nm, tier1)
       resp=requests.get(url, auth=self.auth, headers=self.headers, verify=False)
       payload=json.loads(resp.content)
       path=payload['results'][0]['edge_cluster_path'].split('/')
       path[-1]=ec
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
    parser.add_argument('--ec1id',
                        help='edge cluster id',
                        required=True, default=False)
    parser.add_argument('--t11c',
                        help='number of T1s to migrate',
                        required=True, default=False)
    parser.add_argument('--ec2id',
                        help='edge cluster id',
                        required=True, default=False)
    parser.add_argument('--t12c',
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
#    ecid = args.ec1id
    t11c = int(args.t11c)
    t12c = int(args.t12c)
    t11=True
    t12=False
    obj=EcMove(nm,nu,np)
    if  obj.ver:

      with open("/var/log/policy/localhost_access_log.txt", 'r') as file:
        l=[]
        word=['t1','locale-services','virtual']
        for line in follow(file):
            if all(x in line for x in word):
               l.append(line)
      #the idea here is to move atleast half of the T1's to the second edge cluster, if customer has 400+ T1's we will pass t1c count as 200
      #so that half of the T1's move to second EC and remaining will stay on default cluster. wouldnt pose any capacity issues.
               if  t11 and len(l)==t11c:
                  t = Thread(target=obj._update_edge_clust, args=(l,args.ec1id))
                  t.start()
                  t11=False
                  t12=True
                  l=[]
               if  t12 and len(l)==t12c:
                  obj._update_edge_clust(l,args.ec2id)
                  t.join()
                  break
