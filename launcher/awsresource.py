import boto3


class AWSResourceHandler(object):
    def __init__(self, account_id, boto3_session):
        self.account_id = account_id
        self.session = boto3_session

    def _tag_value(self, obj, key):
        for tag in obj.tags:
            if tag['Key'].lower() == key.lower():
                return tag['Value']
        return None

    def _name_tag(self, obj):
        return self._tag_value(obj, 'name')

    def update_images(self):
        self.images = []
        res = self.session.resource("ec2")
        for image in res.images.filter(Owners=[self.account_id]):
            self.images.append([image.name, image.id, "image"])
        for image in res.images.filter(ExecutableUsers=[self.account_id]):
            self.images.append([image.name, image.id, "image", None])
        return self.images

    def update_keypairs(self):
        self.key_pairs = []
        res = self.session.resource("ec2")
        for key_pair in res.key_pairs.all():
            self.key_pairs.append([key_pair.name, key_pair.name, "key_pair", None])
        return self.key_pairs

    def update_instance_profiles(self):
        self.instance_profiles = []
        res = self.session.resource("iam")
        for instance_profile in res.instance_profiles.all():
            self.instance_profiles.append([
                instance_profile.name,
                instance_profile.name,
                "instance_profile",
                instance_profile.arn
            ])
        return self.instance_profiles

    def update_vpcs(self):
        self.vpcs = []
        res = self.session.resource("ec2")
        for vpc in res.vpcs.all():
            self.vpcs.append([self._name_tag(vpc), vpc.id, "vpc", None])
        return self.vpcs

    def update_subnets(self):
        self.subnets = []
        res = self.session.resource("ec2")
        for subnet in res.subnets.all():
            self.subnets.append([
                self._name_tag(subnet),
                subnet.id,
                'subnet',
                None,
                subnet.vpc_id
            ])
        return self.subnets

    def update_security_groups(self):
        self.security_groups = []
        res = self.session.resource("ec2")
        for sg in res.security_groups.all():
            self.security_groups.append([
                sg.group_name,
                sg.id,
                'security_group',
                None,
                sg.vpc_id
            ])
        return self.security_groups

    def update_server_certificates(self):
        self.server_certificates = []
        res = self.session.resource("iam")
        for cert in res.server_certificates.all():
            self.server_certificates.append([
                cert.name,
                cert.name,
                'server_certificate',
                cert.server_certificate_metadata['Arn']
            ])
        return self.server_certificates


def main():

    import json
    def pprint(obj):
        print(json.dumps(obj, indent=2))

    account_id = "681545073814"
    boto3_session = boto3.Session(profile_name="cn-alpha")
    arh = AWSResourceHandler(account_id, boto3_session)
    #pprint(arh.update_images())
    #pprint(arh.update_keypairs())
    #pprint(arh.update_instance_profiles())
    #pprint(arh.update_vpcs())
    #pprint(arh.update_subnets())
    #pprint(arh.update_security_groups())
    pprint(arh.update_server_certificates())

if __name__ == "__main__":
    main()