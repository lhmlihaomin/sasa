function showStartMessage(msg) {
    window.msg = Messenger().post({
        message: msg,
        type: "info"
    });
}


function showResultMessage(msg) {
    window.msg = Messenger().post({
        message: msg,
        type: "success"
    });
}


function showErrorMessage(msg) {
    Messenger().post({
        message: msg,
        showCloseButton: true,
        type: "error"
    });
}


function getRegionsForProfile() {
    var profileId = $("#selProfile").val();
    var selRegions = $('#selRegions');
    if (profileId == 0) {
        selRegions.empty();
        var option = $('<option></option>').html("---")
                                           .prop("value", 0);
        selRegions.append(option);
        return false;
    }
    showStartMessage("Loading Regions...");
    $.ajax({
        url: "get_regions_for_profile/"+profileId+"/",
        dataType: "json",
        success: listRegions
    })
}


function listRegions(regions) {
    var selRegions = $('#selRegions');
    selRegions.empty();
    for (var i=0; i<regions.length; i++) {
        var option = $('<option></option>').html(regions[i].full_name)
                                           .prop("value", regions[i].id);
        selRegions.append(option);
    }
    showResultMessage("Regions loaded.")
}


function updateNextResources() {
    updateResourceIndex++;
    if (updateResourceIndex >= resourceTypes.length) {
        showResultMessage("Resources have been updated.");
        return;
    }
    
    showStartMessage("updating "+resourceTypes[updateResourceIndex]+"...");
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    $.ajax({
        method: "post",
        url: "./update_resource/",
        data: {
            profile_id: profileId,
            region_id: regionId,
            resource_type: resourceTypes[updateResourceIndex]
        },
        success: updateNextResources
    })
}


function beginUpdateResources() {
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return;
    }
    updateResourceIndex = -1;
    showStartMessage("Clearing resources...");
    
    $.ajax({
        method: "post",
        url: "./clear_resources/",
        data: {
            profile_id: profileId,
            region_id: regionId,
        },
        dataType: "json",
        success: updateNextResources
    })
}


function listResources() {
    function showListResources(data) {
        var tbody = $('#tbodyAWSResources');
        for (var i=0; i<data.length; i++) {
            var item = data[i];
            var tr = $('<tr></tr>')
                .append($('<td></td>').html(item.name))
                .append($('<td></td>').html(item.resource_id))
                .append($('<td></td>').html(item.resource_type))
                .append($('<td></td>').html(item.arn))
                .append($('<td></td>').html(item.parent));
            tr.appendTo(tbody);
        }
        $('#modalResources').modal();
    }

    var tbody = $('#tbodyAWSResources');
    tbody.empty()

    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $.ajax({
        url: "./list_resources/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId
        },
        dataType: "json",
        success: showListResources
    });
}


function listEC2LaunchOptionSets() {
    function makeModulePanel(module) {
        if ($('#panelBody_'+module).length) {
            return $('#panelBody_'+module);
        } else {
            var panelHeading = $('<div></div>').addClass("panel-heading").html(module);
            var panelBody = $('<div></div>').addClass("panel-body").prop("id", "panelBody_"+module);
            var moduleTable = $('<table></table>')
                .addClass("table table-hover")
                .append($('<thead><tr><th>MODULE</th><th>VERSION</th><th>REGION</th><th>AZ</th><th style="width:80px;"></th></tr></thead>'))
                .append($('<tbody></tbody>').prop('id', 'tbody_'+module))
                .appendTo(panelBody);
            var panelModule = $('<div></div>')
                .addClass("panel panel-primary")
                .append(panelHeading)
                .append(panelBody)
                .appendTo($('#divEC2LaunchOptionSetList'));
        }
    }
    function showListEC2LaunchOptionSets(data) {
        for (var i=0;i<data.length;i++) {
            var module = data[i].module;
            var panelBody = makeModulePanel(module);
            var tbody = $('#tbody_'+module);
            /*var tdActions = $('<td></td>')
                .append(
                    $('<button></button>')
                        .addClass('btn btn-primary')
                        .css("margin-right", "2px")
                        .append($('<i></i>').addClass('fa fa-list'))
                        .prop("title", "Detail")
                        .attr("onclick", "viewEC2LaunchOptionSet("+data[i].id+")")
                )
                .append(
                    $('<button></button>')
                        .addClass('btn btn-primary')
                        .css("margin-right", "2px")
                        .append($('<i></i>').addClass('fa fa-arrow-up'))
                        .prop("title", "Update to new version")
                        .attr("onclick", "listImagesForModule("+data[i].id+")")
                )
                .append(
                    $('<button></button>')
                        .addClass('btn btn-success')
                        .append($('<i></i>').addClass('fa fa-play'))
                        .prop("title", "Run")
                        .attr("onclick", "runInstances("+data[i].id+")")
                )*/

            var tdActions = $(
'<td><div class="btn-group">\
    <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown">\
Action <span class="caret"></span>\
    </button>\
    <ul class="dropdown-menu" role="menu">\
        <li><a class="actionLink" onclick="viewEC2LaunchOptionSet('+data[i].id+')"><i class="fa fa-list"></i> View & Edit</a></li>\
        <li><a class="actionLink" onclick="listImagesForModule('+data[i].id+')"><i class="fa fa-arrow-up"></i> Update Version</a></li>\
        <li><a class="actionLink" onclick="runInstances('+data[i].id+')"><i class="fa fa-play"></i> Run Instances</a></li>\
    </ul>\
</div></td>');

            var tr = $('<tr></tr>')
                .append('<td>'+data[i].module+'</td>')
                .append('<td>'+data[i].version+'</td>')
                .append('<td>'+data[i].region+'</td>')
                .append('<td>'+data[i].az+'</td>')
                .append(tdActions)
                .appendTo(tbody);
                 
        }
    }

    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $('#divEC2LaunchOptionSetList').empty();
    $.ajax({
        url: "./list_ec2launchoptionsets/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId
        },
        dataType: "json",
        success: showListEC2LaunchOptionSets
    });
}


function viewEC2LaunchOptionSet(setId) {
    function showEC2LaunchOptionSet(data) {
        /*
        editor.setValue("");
        editor.setValue(data.content);
        window.EC2LaunchOptionSetId = data.id;*/
        //$("#modalViewEC2LaunchOptionSet").modal();
        $('#divEC2LaunchOptionSetTitle')
            .html("DETAIL: "+[data.environ, data.module, data.version, data.region, data.az].join("-"));
        editor.setValue("");
        editor.setValue(data.content);
        window.EC2LaunchOptionSetId = data.id;
        $('#modalDetail').modal();
        $('#a_detail').tab('show');
    }
    $.ajax({
        url: "./view_ec2launchoptionset/",
        method: "post",
        data: {
            id: setId
        },
        dataType: "json",
        success: showEC2LaunchOptionSet
    })
}


function saveEC2LaunchOptionSet() {
    var txt = editor.getValue();
    // check EC2LaunchOptionSetId:
    if (EC2LaunchOptionSetId == 0) {
        showErrorMessage("Nothing loaded. Cannot save now.");
        return false;
    }
    // check JSON syntax:
    try {
        JSON.parse(txt);
    } catch (e) {
        showErrorMessage("Your input is not valid JSON.");
        return false;
    }
    $.ajax({
        url: "save_ec2launchoptionset/",
        method: "post",
        data: {id: EC2LaunchOptionSetId, content: txt},
        dataType: "json",
        success: function() {
            showResultMessage("Save successful.");
            viewEC2LaunchOptionSet(EC2LaunchOptionSetId);
        },
        error: function() {showErrorMessage("Save failed.");}
    })
    console.log(EC2LaunchOptionSetId)
}


function runEC2LaunchOptionSet(setId) {
    console.log(setId);
}


function showDialogEC2LaunchOptionSet() {
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $('#modalNew').modal();
}


function newEC2LaunchOptionSet() {
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }

    var module = $('#iModule').val();
    var version = $('#iVersion').val();
    var az = $('#iAZ').val();
    var txt = editorNew.getValue();

    $.ajax({
        url: "./new_ec2launchoptionset/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId,
            module: module,
            version: version,
            az: az,
            content: txt
        },
        dataType: "json",
        success: function(data) {
            if (data) {
                $('#modalNew').modal('hide');
                listEC2LaunchOptionSets();
            } else {
                showErrorMessage("Failed to create EC2LaunchOptionSet. Please check your input.");
            }
        }
    })
}


function listImagesForModule(setId) {
    function showUpdateVersion(data) {
        var sel = $('#selListImagesForModule');
        sel.empty();
        for (var i=0;i<data.length;i++) {
            $('<option></option>')
                .html(data[i].name+" ("+data[i].resource_id+")")
                .attr('value', data[i].id)
                .appendTo(sel);
        }
        //$('#modalUpdateVersion').modal();
        //$('#divHeadingUpdateVersion')
        //    .html([data.environ, data.module, data.version, data.region, data.az].join("-"));
        window.EC2LaunchOptionSetId = setId;
        $('#modalDetail').modal();
        $('#a_ami_versions').tab('show');
    }

    window.EC2LaunchOptionSetId = setId;
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $.ajax({
        url:"list_all_images_for_module/",
        method: "post",
        data:{
            profile_id: profileId,
            region_id: regionId,
            id:setId
        },
        dataType:"json",
        success: showUpdateVersion
    })
}


function updateEC2LaunchOptionSet() {
    function onUpdateSuccess(data) {
        if (data) {
            listEC2LaunchOptionSets();
        }
    }

    var imageId = $('#selListImagesForModule').val();
    $.ajax({
        url:"./update_ec2launchoptionset/",
        method:"post",
        dataType:"json",
        data:{
            id:EC2LaunchOptionSetId,
            image_id:imageId
        },
        success:onUpdateSuccess
    })
}


function runInstances(setId) {
    function onRunInstancesSuccess(data) {
        var instance_ids = data;
        showResultMessage("These instances has been launched: "+instance_ids);
        addInstanceTags(instance_ids);
    }

    window.EC2LaunchOptionSetId = setId;
    var num = Number(prompt("Input instance count:"))
    if (isNaN(num)) {
        showErrorMessage("Please input a number.");
        return false;
    }
    num = Math.floor(num);
    if (num <= 0) {
        showErrorMessage("Instance count must be greater than 0.");
        return false;
    }

    showStartMessage("Launching instances ...");
    $.ajax({
        url:"./run_instances/",
        method:"post",
        dataType:"json",
        data:{
            set_id:setId,
            count: num
        },
        success: onRunInstancesSuccess
    })
}


function addInstanceTags(instance_ids) {
    function onAddInstanceTagsSuccess(data) {
        var txt = "Instance tags: ";
        var instance_ids = [];
        for (var key in data) {
            txt += " ["+key+": "+data[key]+"] ";
            instance_ids.push(key)
        }
        showResultMessage(txt)
        addVolumeTags(instance_ids)
    }

    showStartMessage("Applying tags to instances: "+instance_ids);
    $.ajax({
        url:"./add_instance_tags/",
        method:"post",
        dataType:"json",
        data:{
            set_id: window.EC2LaunchOptionSetId,
            instance_ids: instance_ids
        },
        success: onAddInstanceTagsSuccess
    })
}


function addVolumeTags(instance_ids) {
    function onAddVolumeTagsSuccess(data) {
        var txt = "Instance volume tags: ";
        var instance_ids = [];
        for (var key in data) {
            txt += " ["+key+": "+data[key]+"] ";
            instance_ids.push(key)
        }
        showResultMessage(txt)
    }

    showStartMessage("Applying tags to instance volumes: "+instance_ids)
    $.ajax({
        url:"./add_volume_tags/",
        method:"post",
        dataType:"json",
        data:{
            set_id: window.EC2LaunchOptionSetId,
            instance_ids: instance_ids
        },
        success: onAddVolumeTagsSuccess
    })
}
/*$.ajax({
  url:"./add_instance_tags/",
  method:"post",
  dataType:"json",
  data:{
    set_id:125,
    instance_ids:["i-cccafaf4", "i-cfcafaf7"]
  },
  success:console.log
})*/
