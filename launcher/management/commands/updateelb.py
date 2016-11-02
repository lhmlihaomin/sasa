import json

import boto3
from django.core.management.base import BaseCommand, CommandError
from launcher.models import ELBGenericUpdateTask, Profile, Region

class Command(BaseCommand):
    help = "Handle ELB related background tasks."

    def handle(self, *args, **options):
        """for task in ELBGenericUpdateTask.objects.all():
            task.delete()
        task = ELBGenericUpdateTask()
        task.id = 1
        task.elb_name = "dev-elb-test"
        task.profile = Profile.objects.get(pk=4)
        task.region = Region.objects.get(pk=4)
        task.instances_reg =   '["i-9ad2eba2", "i-9bd2eba3"]'
        task.instances_dereg = '["i-98d2eba0", "i-99d2eba1"]'
        #task.instances_reg =   '["i-98d2eba0", "i-99d2eba1"]'
        #task.instances_dereg = '["i-9ad2eba2", "i-9bd2eba3"]'
        task.finished = False
        task.confirmed = False
        task.stage = 0
        task.save()
        self.stdout.write("TASK CREATED.")
        return"""

        tasks = ELBGenericUpdateTask.objects.exclude(stage=3)
        for task in tasks:
            self.stdout.write(task.elb_name)
            self.stdout.write(task.profile.name)
            self.stdout.write(task.region.code)
            session = boto3.Session(
                profile_name = task.profile.name,
                region_name = task.region.code
            )
            elbclient = session.client("elb")
            self.stdout.write(str(task.stage))
            if task.stage == 0:
                # register new instances.
                result = self.register_instances(task, elbclient)
                # set new stage
                if result:
                    task.instances_registered()
                    task.save()
            elif task.stage == 1:
                # check instance health:
                result = self.check_instance_health(task, elbclient)
                # if all InService, remove old:
                if result:
                    task.instances_inservice()
                    task.save()
                    result_dereg = self.deregister_instances(task, elbclient)
                    # set new stage.
                    if result_dereg:
                        task.instances_deregistered()
                        task.finished = True
                        task.save()
            elif task.stage == 2:
                # check if old instances have been removed:
                # set new stage
                pass
        raw_input()

    def register_instances(self, task, elbclient):
        instance_ids = json.loads(task.instances_reg)
        list_dict_instance_ids = list(map(
            lambda x:{'InstanceId': x},
            instance_ids
        ))
        self.stdout.write("Registering new instances ...")
        if len(list_dict_instance_ids) == 0:
            return True
        try:
            resp = elbclient.register_instances_with_load_balancer(
                LoadBalancerName=task.elb_name,
                Instances=list_dict_instance_ids
            )
        except Exception as ex:
            raise ex
        # check if every instance has been registered:
        new_instance_ids = list(map(
            lambda x:x['InstanceId'],
            resp['Instances']
        ))
        for instance_id in instance_ids:
            if instance_id not in new_instance_ids:
                return False
        return True

    def check_instance_health(self, task, elbclient):
        instance_ids = json.loads(task.instances_reg)
        list_dict_instance_ids = list(map(
            lambda x:{'InstanceId': x},
            instance_ids
        ))
        self.stdout.write("Checking instance health states ...")
        try:
            resp = elbclient.describe_instance_health(
                LoadBalancerName=task.elb_name,
                Instances=list_dict_instance_ids
            )
        except Exception as ex:
            raise ex
        for InstanceState in resp['InstanceStates']:
            if InstanceState['State'] != "InService":
                return False
        return True

    def deregister_instances(self, task, elbclient):
        instance_ids = json.loads(task.instances_dereg)
        list_dict_instance_ids = list(map(
            lambda x:{'InstanceId': x},
            instance_ids
        ))
        self.stdout.write("Deregistering old instances ...")
        if len(list_dict_instance_ids) == 0:
            return True
        try:
            resp = elbclient.deregister_instances_from_load_balancer(
                LoadBalancerName=task.elb_name,
                Instances=list_dict_instance_ids
            )
        except Exception as ex:
            raise ex
        # check if every instance has been deregistered:
        new_instance_ids = list(map(
            lambda x:x['InstanceId'],
            resp['Instances']
        ))
        for instance_id in instance_ids:
            if instance_id in new_instance_ids:
                return False
        return True
