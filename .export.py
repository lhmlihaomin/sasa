import sqlite3
from os import path
import json

PWD = path.abspath(path.dirname(__file__))
SAVEPATH = path.sep.join([PWD, 'json'])
print("Saving JSON files to %s ..."%(SAVEPATH,))

sql = """
select 
    launcher_profile.name, 
    launcher_region.code, 
    launcher_ec2launchoptionset.module, 
    launcher_ec2launchoptionset.version,
    launcher_ec2launchoptionset.content 
from 
    launcher_ec2launchoptionset,
    launcher_profile,
    launcher_region 
where 
    launcher_ec2launchoptionset.profile_id=launcher_profile.id 
and launcher_ec2launchoptionset.region_id=launcher_region.id
"""

db = sqlite3.connect('db.sqlite3')
c = db.cursor()
c.execute(sql)
data = c.fetchall()
for row in data:
    profile, region, module, version, content = row
    fname = "%s.%s.%s-%s.json"%(profile, region, module, version)
    fname = path.sep.join([SAVEPATH, fname])
    with open(fname, 'w') as fp:
        print("Saving %s ..."%(fname,))
        fp.write(content)
        