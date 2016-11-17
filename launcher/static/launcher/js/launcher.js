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
        url: "/launcher/get_regions_for_profile/"+profileId+"/",
        dataType: "json",
        success: listRegions
    })
}


function listRegions(regions) {
    var selRegions = $('#selRegions');
    selRegions.empty();
    $('<option selected>---</option>').appendTo(selRegions);
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
        method: "get",
        data: {
            profile_id: profileId,
            region_id: regionId
        },
        dataType: "json",
        success: showListResources
    });
}


function listEC2LaunchOptionSets(moduleName) {
    function makeModulePanel(module) {
        if ($('#panelBody_'+module).length) {
            return $('#panelBody_'+module);
        } else {
            //var panelHeading = $('<div></div>').addClass("panel-heading").html(module);
            var panelTitle = $('<a class="panelToggle" href="#" >'+module+'</a>')
                .click(function(){
                    togglePanelBody(this)})
            var panelHeading = $('<div></div>').addClass("panel-heading").append(panelTitle);
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
            return panelBody;
        }
    }
    function showListEC2LaunchOptionSets(data) {
        for (var i=0;i<data.length;i++) {
            var module = data[i].module;
            var panelBody = makeModulePanel(module);
            var tbody = $('#tbody_'+module);

            var tdActions = $(
'<td><div class="btn-group">\
    <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown">\
Action <span class="caret"></span>\
    </button>\
    <ul class="dropdown-menu" role="menu">\
        <li><a class="actionLink" onclick="viewEC2LaunchOptionSet('+data[i].id+')"><i class="fa fa-edit"></i> View & Edit</a></li>\
        <li><a class="actionLink" onclick="listImagesForModule('+data[i].id+')"><i class="fa fa-arrow-up"></i> Update Version</a></li>\
        <li><a class="actionLink" onclick="listInstancesForEC2LaunchOptionSet('+data[i].id+')"><i class="fa fa-list"></i> Manage Instances</a></li>\
        <li><a class="actionLink" onclick="deleteEC2LaunchOptionSet('+data[i].id+')"><i class="fa fa-trash-o"></i> Delete</a></li>\
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

    if (typeof moduleName == "undefined") {
        moduleName = "";
    }
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    if (moduleName == "") {
        $('#divEC2LaunchOptionSetList').empty();
    } else {
        $('#tbody_'+moduleName).empty()
    }
    console.log("HAHAHA "+moduleName);
    $.ajax({
        url: "./list_ec2launchoptionsets/",
        method: "get",
        data: {
            profile_id: profileId,
            region_id: regionId,
            module_name: moduleName
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
        // clear online instances in table, becausing we are changing active optionset:
        clearOnlineInstances();
        $('#modalDetail').modal();
        $('#a_detail').tab('show');
    }
    $.ajax({
        url: "./view_ec2launchoptionset/",
        method: "get",
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


function deleteEC2LaunchOptionSet(setId) {
    if (!confirm("Are you sure to [DELETE] this object?")) {
        return false;
    }

    $.ajax({
        url: './delete_ec2launchoptionset/',
        method: 'post',
        dataType: 'json',
        data: {
            set_id: setId
        },
        success: function() {
            showResultMessage("Object deleted.");
            listEC2LaunchOptionSets();
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
    // clear online instances in table, becausing we are changing active optionset:
    clearOnlineInstances();
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $.ajax({
        url:"list_all_images_for_module/",
        method: "get",
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
        if (data[0]) {
            listEC2LaunchOptionSets(data[1]);
        } else {
            showErrorMessage(data[1]);
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
        showResultMessage(txt);
        // clear online instances in table, becausing we are changing active optionset:
        clearOnlineInstances();
        refreshOnlineInstances(window.EC2LaunchOptionSetId);
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


function clearOnlineInstances() {
    $('#spanOnlineInstances').html('(Click "Refresh" to load instances)');
    var tbody = $('#tbodyOnlineInstances');
    tbody.empty();
}


function refreshOnlineInstances(setId) {
    function showListInstancesForEC2LaunchOptionSet(data) {
        var tbody = $('#tbodyOnlineInstances');
        tbody.empty();
        $('#spanOnlineInstances').html("ONLINE INSTANCES: "+data.length);
        for (var i=0; i<data.length; i++) {
            var chk = $('<input type="checkbox" name="instance_id[]" value="'+data[i].id+'" class="instanceChk"/>')
            var btnStart = $('<button class="btn btn-primary" title="Start"><i class="fa fa-play"></i></button>')
                .click(function(i) {return function() {startInstance(data[i].id);}}(i));
            var btnStop = $('<button class="btn btn-primary" title="Stop"><i class="fa fa-stop"></i></button>')
                .click(function(i) {return function() {stopInstance(data[i].id);}}(i));
            var btnTerminate = $('<button class="btn btn-primary" title="Terminate"><i class="fa fa-trash-o"></i></button>')
                .click(function(i) {return function() {terminateInstance(data[i].id);}}(i));
            var tr = $('<tr></tr>');
            var chkTd = $('<td></td>').append(chk)
            tr.append(chkTd)
              .append($('<td>'+data[i].id+'</td>'))
              .append($('<td>'+data[i].name+'</td>'))
              .append($('<td>'+data[i].state+'</td>'));
            /*var tr = $('<tr><td>'
                +data[i].id+'</td><td>'
                +data[i].name+'</td><td>'
                +data[i].state+'</td></tr>');*/
            var td = $('<td></td>')
                .append(btnStart)
                .append(btnStop)
                .append(btnTerminate)
                .appendTo(tr)
            tr.appendTo(tbody);
        }

        $('.instanceChk').click(function(event) {
        var checkboxes = $('.instanceChk');
        if (event.shiftKey) {
            if (!lastCheckbox) return true;
            var m = checkboxes.index(lastCheckbox);
            var n = checkboxes.index(this);
            var selectedCheckboxes = checkboxes.slice(
                Math.min(m, n),
                Math.max(m, n)
            );
            console.log($(this).prop('checked'));
            $(lastCheckbox).prop('checked', $(this).prop('checked'));
            selectedCheckboxes.prop('checked', $(this).prop('checked'));
        } else {
            lastCheckbox = this;
        }
        console.log(lastCheckbox);
    });
    }

    window.EC2LaunchOptionSetId = setId;
    clearOnlineInstances();
    if (setId == 0) {
        showErrorMessage("Nothing selected.");
        return;
    }
    $('#spanOnlineInstances').html("LOADING ...");
    $.ajax({
        url: './list_instances_for_ec2launchoptionset/',
        method: 'get',
        data: {
            set_id: setId
        },
        dataType: 'json',
        success: showListInstancesForEC2LaunchOptionSet
    })
}


function listInstancesForEC2LaunchOptionSet(setId) {
    $('#modalDetail').modal();
    $('#a_instances').tab('show');

    refreshOnlineInstances(setId);
}


function startInstance(instanceId) {
    if (!confirm("Are you sure to [START] instance: "+instanceId+"?")) {
        return false;
    }
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $.ajax({
        url: "./start_instance/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId,
            instance_id: instanceId,
        },
        dataType: "json",
        success: function(data){
            alert(data);
            refreshOnlineInstances(window.EC2LaunchOptionSetId);
        }
    })
}


function stopInstance(instanceId) {
    if (!confirm("Are you sure to [STOP] instance: "+instanceId+"?")) {
        return false;
    }
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $.ajax({
        url: "./stop_instance/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId,
            instance_id: instanceId,
        },
        dataType: "json",
        success: function(data){
            alert(data);
            refreshOnlineInstances(window.EC2LaunchOptionSetId);    
        }
    })
}


function terminateInstance(instanceId) {
    if (!confirm("Are you sure to [TERMINATE] instance: "+instanceId+"?")) {
        return false;
    }
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    $.ajax({
        url: "./terminate_instance/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId,
            instance_id: instanceId,
        },
        dataType: "json",
        success: function(data){
            alert(data);
            refreshOnlineInstances(window.EC2LaunchOptionSetId);
        }
    })
}


function stopSelectedInstances() {
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    var instanceIds = [];
    $('.instanceChk').each(function(index, e) {
        if ($(e).prop('checked')) {
            instanceIds.push($(e).prop('value'));
        }
    })
    if (instanceIds.length <= 0) {
        showErrorMessage("No instances selected.");
        return false;
    }
    if (!confirm("Are you sure to [STOP] selected instances?")) {
        return false;
    }
    $.ajax({
        url: "./stop_instances/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId,
            instance_ids: instanceIds
        },
        dataType: "json",
        success: function(data){
            alert(data);
            refreshOnlineInstances(window.EC2LaunchOptionSetId);
        }
    })
}


function terminateSelectedInstances() {
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    var instanceIds = [];
    $('.instanceChk').each(function(index, e) {
        if ($(e).prop('checked')) {
            instanceIds.push($(e).prop('value'));
        }
    })
    if (instanceIds.length <= 0) {
        showErrorMessage("No instances selected.");
        return false;
    }
    if (!confirm("Are you sure to [TERMINATE] selected instances?")) {
        return false;
    }
    $.ajax({
        url: "./terminate_instances/",
        method: "post",
        data: {
            profile_id: profileId,
            region_id: regionId,
            instance_ids: instanceIds
        },
        dataType: "json",
        success: function(data){
            alert(data);
            refreshOnlineInstances(window.EC2LaunchOptionSetId);
        }
    })
}


function stopAllInstances() {
    var setId = window.EC2LaunchOptionSetId;
    if (0 == setId) {
        showErrorMessage("Nothing selected.");
        return false;
    }
    if (!confirm("Are you sure to [STOP ALL] instances?")) {
        return false;
    }
    $.ajax({
        url: "./stop_all_instances/",
        method: "post",
        data: {
            set_id: setId
        },
        dataType: "json",
        success: function(data){
            alert(data);
            refreshOnlineInstances(window.EC2LaunchOptionSetId);
        }
    })
}


function togglePanelBody(a) {
    // a.parent: panel-heading;
    // a.parent.next: panel-body;
    $(a).parent().next().toggle();
}


function toggleEC2launchOptionSetListPanelBodies() {
    $('#divEC2LaunchOptionSetList .panel-body').toggle();
}

/**
 * ELB functions:
 */
function updateELBs() {
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }

    showStartMessage("Updating ELBs ...");
    $.ajax({
        type: "post",
        url: "./update_elbs/",
        data: {
            profile_id: profileId,
            region_id: regionId
        },
        dataType: "json",
        success: function (response) {
            if (response) {
                showResultMessage("ELBs updated.");
            }
        }
    });
}


function getDistinctModuleNames() {
    function showDistinctModuleNames(data) {
        var sel = $('#selModules');
        sel.empty();
        $('<option selected>---</option>').appendTo(sel);
        for (var i=0; i<data.length; i++) {
            $('<option></option>')
                .prop("value", data[i])
                .html(data[i])
                .appendTo(sel)
        }
    }

    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }

    $.ajax({
        type: "get",
        url: "./get_distinct_module_names/",
        data: {
            profile_id: profileId,
            region_id: regionId
        },
        dataType: "json",
        success: showDistinctModuleNames
    });
}


function getModuleVersions() {
    function showModuleVersions(data) {
        var sel = $('#selVersions')
        sel.empty();
        $('<option selected>---</option>').appendTo(sel);
        for (var i=0; i<data.length; i++) {
            $('<option></option>')
                .html(data[i][0])
                .prop("value", data[i][1])
                .appendTo(sel);
        }
    }

    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    var moduleName = $('#selModules').val()
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }

    $.ajax({
        type: "get",
        url: "./get_module_versions/",
        data: {
            profile_id: profileId,
            region_id: regionId,
            module: moduleName
        },
        dataType: "json",
        success: showModuleVersions
    });
}


function getModuleInstances() {
    function showModuleInstances(data) {
        var tbody = $('#tbodyAddInstances');
        tbody.empty();
        for (var i=0; i<data.length; i++) {
            var input = $('<input type="checkbox" name="instances_reg[]" />')
                .prop('value', data[i].id)
            $('<tr></tr>')
                .append($('<td></td>').append(input))
                .append('<td>'+data[i].id+'</td>')
                .append('<td>'+data[i].name+'</td>')
                .append('<td>'+data[i].state+'</td>')
                .appendTo(tbody);
        }
    }
    
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    var setId = $('#selVersions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }

    $.ajax({
        type: "get",
        url: "./get_module_instances/",
        data: {
            profile_id: profileId,
            region_id: regionId,
            set_id: setId
        },
        dataType: "json",
        success: showModuleInstances
    });
}


function getELBs() {
    function showELBs(data) {
        var sel = $('#selELBs');
        sel.empty();
        $('<option selected>---</option>').appendTo(sel);
        for (var i=0; i<data.length; i++) {
            $('<option></option>')
                .html(data[i])
                .appendTo(sel);
        }
    }

    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }

    $.ajax({
        type: "get",
        url: "./get_elbs/",
        data: {
            profile_id: profileId,
            region_id: regionId
        },
        dataType: "json",
        success: showELBs
    });
}


function getELBInstances() {
    function showELBInstances(data) {
        var tbody = $('#tbodyRemoveInstances');
        tbody.empty();
        for (var i=0; i<data.length; i++) {
            var input = $('<input type="checkbox" name="instances_dereg[]" />')
                .prop('value', data[i].id)
            $('<tr></tr>')
                .append($('<td></td>').append(input))
                .append('<td>'+data[i].id+'</td>')
                .append('<td>'+data[i].name+'</td>')
                .append('<td>'+data[i].state+'</td>')
                .appendTo(tbody);
        }
    }

    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    var elbName = $('#selELBs').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }

    $.ajax({
        type: "get",
        url: "./get_elb_instances/",
        data: {
            profile_id: profileId,
            region_id: regionId,
            elb: elbName
        },
        dataType: "json",
        success: showELBInstances
    });
}


function selRegionsChanged() {
    getDistinctModuleNames();
    getELBs();
}


function startELBGenericUpdateTask() {
    var profileId = $('#selProfile').val();
    var regionId = $('#selRegions').val();
    var elbName = $('#selELBs').val();
    if (profileId == 0 || regionId == 0) {
        showErrorMessage("You need to select a profile/region first.");
        return false;
    }
    var instancesReg = []
    var inputs = $('input[name=instances_reg\\[\\]]')
    for (var i=0; i<inputs.length; i++) {
        if (inputs[i].checked) {
            instancesReg.push($(inputs[i]).val());
        }
    }
    var instancesDereg = []
    var inputs = $('input[name=instances_dereg\\[\\]]')
    for (var i=0; i<inputs.length; i++) {
        if (inputs[i].checked) {
            instancesDereg.push($(inputs[i]).val());
        }
    }
    console.log(instancesReg);
    console.log(instancesDereg);

    $.ajax({
        type: "post",
        url: "./start_elb_generic_update_task/",
        data: {
            profile_id: profileId,
            region_id: regionId,
            elb_name: elbName,
            instances_reg: instancesReg,
            instances_dereg: instancesDereg
        },
        dataType: "json",
        success: function (response) {
            
        }
    });
}

function toggleInstanceCheckboxes() {
    var chk = $('#iToggleInstancesCheck');
    if (chk.prop('checked')) {
        $('.instanceChk').prop('checked', true);
    } else {
        $('.instanceChk').prop('checked', false);
    }
}