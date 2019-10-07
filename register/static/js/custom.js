function deleteAction(url, token){
    
    $.get(url, function(){
    })
        
    .done(function(data){
        $(".modal > .modal-content").html(data);
        $(".modal").addClass("is-active");
        $(".modal .modal-content button.is-danger").click(function(){
            $(".modal").removeClass("is-active");
        });
        
        $("#delete-form").submit(function (event) {
            event.preventDefault();
            
            $.ajaxSetup({
               beforeSend: function(xhr){
                   xhr.setRequestHeader("X-CSRFToken", token);
               }
            });
            
            $.post(url)
            
            .done(function(data) {
                location.reload();
            });
        })
        
    })
        
    .fail(function(xhr){
        alert("Failed");
    });
    
    $(".modal-close, .modal-background").click(function(){
        $(".modal").removeClass("is-active");
    });
}

function updateAction(url, token){
    
    $.get(url, function(){
    })
        
    .done(function(data){
        $(".modal > .modal-content").html(data);
        $(".modal").addClass("is-active");
        $(".modal .modal-content button.is-danger").click(function(){
            $(".modal").removeClass("is-active");
        });
        
        $("#update-form").submit(function (event) {
            event.preventDefault();
            
            $.ajaxSetup({
               beforeSend: function(xhr){
                   xhr.setRequestHeader("X-CSRFToken", token);
               }
            });
            
            $.post(url)
            
            .done(function(data) {
                //location.reload();
            });
        })
        
    })
        
    .fail(function(xhr){
        alert("Failed");
    });
    
    $(".modal-close, .modal-background").click(function(){
        $(".modal").removeClass("is-active");
    });
}


function btnCollapsed(){
    $('button#btn_collapsed').click(function () {
        $('#collpase-nave').addClass('collapsed');
        $('#collapsed-icon').addClass('is-active');
        $('#collapsed-icon').removeClass('is-inactive');
        $('button#btn_collapsed').addClass('is-inactive');
        $('button#btn_collapsing').removeClass('is-inactive');
        $('#collapse-body').addClass('collapsed-body');
    });
}

function btnCollapsing(){
    $('button#btn_collapsing').click(function () {
        $('#collpase-nave').removeClass("collapsed");
        $('#collapsed-icon').removeClass("is-active");
        $('#collapsed-icon').addClass("is-inactive");
        $('button#btn_collapsing').addClass("is-inactive");
        $('button#btn_collapsed').removeClass("is-inactive");
        $('#collapse-body').removeClass("collapsed-body");
    });
    
}


