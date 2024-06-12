$(document).ready(function(){
    viewer.init();
    toolbar.init();
    spinebar.init();
  });

var viewer = {
    init: function() {
        viewer.sd = new SD('assets');
        viewer.searchResults = charData;
        viewer.currentBG = "../assets/bg/zgreen.png";
        viewer.mouse = false;
        viewer.lastMouseX = 0;
        viewer.lastMouseY = 0;
        viewer.scale = 1.0;

        viewer.canvas = $(".Canvas");
        viewer.selectAnimation = $(".selectAnimation");
        viewer.selectShip = $(".selectShip");
        viewer.selectBG = $(".selectBG");

        viewer.selectedSpine = -1;
        viewer.spine = [];

        viewer.selectAnimation.change(function() {
            viewer.changeAnimation(this.selectedIndex);
        });

        viewer.app = new PIXI.Application(900, 2000, { backgroundColor: 0x00ff00 });
        viewer.canvas.append($(viewer.app.view));
        viewer.drawBG(viewer.currentBG);   
        $(viewer.app.view).mousedown(() => {
            viewer.mouse = true;
            viewer.lastMouseX = event.clientX - event.target.getBoundingClientRect().left;
            viewer.lastMouseY = event.clientY - event.target.getBoundingClientRect().top;
        });
        $(viewer.app.view).mouseup(() => {viewer.mouse = false});
        $(viewer.app.view).mousemove((event) => {
            var sx = event.clientX - event.target.getBoundingClientRect().left;
            var sy = event.clientY - event.target.getBoundingClientRect().top;
            if(viewer.mouse){
                viewer.spine[viewer.selectedSpine].position.set((sx - viewer.lastMouseX) + viewer.spine[viewer.selectedSpine].position._x, (sy - viewer.lastMouseY) + viewer.spine[viewer.selectedSpine].position._y);

                viewer.lastMouseX = sx;
                viewer.lastMouseY = sy;
            }
        });

        window.onresize = (event) => {
            if (event === void 0) { event = null; }
            $("#mainbody").width(spinebar.spinebar.position().left-40);
            if (document.getElementById("darken") != null){
                document.getElementById("darken").top = window.pageYOffset + "px";
                document.getElementById("selector").top = (window.pageYOffset + (window.innerHeight * 0.05)) + "px";
            }
            var height = Math.max( document.body.scrollHeight, document.body.offsetHeight, 
                               document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );   
            $("#footer").css("top",height - $("#footer").height() - 20);
        };
        $(document).ready(() => {
            $("#mainbody").width(spinebar.spinebar.position().left-40);
            var height = Math.max( document.body.scrollHeight, document.body.offsetHeight, 
                               document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );   
            $("#footer").css("top",height - $("#footer").height() - 20);
            toolbar.toolbar.css("top", window.pageYOffset);
        });
        $(window).scroll(function(){
            toolbar.toolbar.css("top", window.pageYOffset);
            spinebar.spinebar.css("top", window.pageYOffset);
        });
    },
    changeCanvas : function(skeletonData) {
        viewer.spine.push(new PIXI.spine.Spine(skeletonData));
        viewer.spine[viewer.spine.length-1].name = skeletonData.name;
        viewer.selectedSpine = viewer.spine.length - 1;
        
        if (viewer.app.stage.children.length <= 1)
            viewer.drawBG(viewer.currentBG);
        viewer.app.stage.addChild(viewer.spine[viewer.selectedSpine]);
        viewer.spine[viewer.selectedSpine].position.set(viewer.app.view.width * 0.5 , viewer.app.view.height * 0.8);
        spinebar.addToSpriteList({"icon":skeletonData.icon,"id":skeletonData.name,"index":viewer.selectedSpine});
    },
    changeAnimation : function(num) {
        var name = viewer.spine[viewer.selectedSpine].spineData.animations[num].name;
        viewer.spine[viewer.selectedSpine].state.setAnimation(0, name, true);
    },
    search : function(filter, filterType, key){
        if (filter != null && filterType != null){
            var temp = {};
            for (var value in viewer.searchResults){
                if (viewer.searchResults[value][filterType] == filter)
                    temp[value] = viewer.searchResults[value];                
            }
            viewer.searchResults = temp;
        }
        if (key != null){
            if (key == 8 || key == 46)
                viewer.searchResults = charData;
        }
        var data = {};
        var r = new RegExp($("#searchField").val().toLowerCase().trim());
        for (var value in viewer.searchResults){
            if (r.test(viewer.searchResults[value].name.toLowerCase()))
                data[value] = viewer.searchResults[value];
        }
        viewer.searchResults = data;
        viewer.loadFilter("type", "#searchType", "#ecd2fc");
        viewer.loadFilter("group", "#searchGroup", "#ccccff");
        viewer.loadResults(viewer.searchResults);
    },
    loadResults : function(data){
        $("#resultContainer").empty();
        for (var value in data){
            $("#resultContainer").append($("<div></div>")
                .addClass("shipIcon")
                .attr("id",value)
                .css("background", "url(https://raw.githubusercontent.com/shadowhurricane/Azur-Lane-Murm/main/assets/qicon/"+data[value].skin[0]+".png)")
                .css("background-size", "70px 70px")
                .mouseover(function(){
                    $(this).css("background-size", "105%");
                })
                .mouseout(function(){
                    $(this).css("background-size", "100%");
                })
                .click(function(){
                    $(document.body).append($("<div></div>")
                        .attr("id","darken2")
                        .addClass("darken")
                        .css("top", window.pageYOffset + "px")
                        .click(function(){
                            $('#darken2').remove();
                            $('#selector2').remove();
                            $(document.body).css("overflow", "auto");
                            viewer.searchResults = charData;
                        })
                    )
                    .append($("<div></div>")
                        .attr("id","selector2")
                        .addClass("selector")
                        .css("top", (window.pageYOffset + (window.innerHeight * 0.05)) + "px")
                    )
                    .css("overflow", "hidden");


                    $("#selector2").append($("<div></div>")
                        .attr("id","skinContainer")
                        .attr("align","center")
                    );

                    for (var x in data[$(this).attr("id")].skin){
                        $("#skinContainer").append($("<div></div>")
                            .addClass("shipIcon")
                            .attr("id",data[$(this).attr("id")].skin[x])
                            .css("background", "url(https://raw.githubusercontent.com/shadowhurricane/Azur-Lane-Murm/main/assets/qicon/"+data[$(this).attr("id")].skin[x]+".png)")
                            .css("background-size", "70px 70px")
                            .click(function(){
                                viewer.activeId = $(this).attr("id");
                                var self = this;
                                $("#skinContainer").children("div").each(function(){
                                    if ($(this).attr("id") == $(self).attr("id"))
                                        $(this).css({"height":"90px","width":"90px","background-size":"100%"});
                                    else
                                        $(this).css({"height":"70px","width":"70px","background-size":"100%"});
                                });
                            })
                        );
                        $("#"+data[$(this).attr("id")].skin[0]).trigger("click");
                    }

                    $("#selector2").append($("<div></div>")
                        .attr("id","ctrlContainer")
                        .attr("align","center")
                        .css("margin-top","10px")
                    );

                    $("#ctrlContainer").append($("<div></div>")
                        .attr("id","skinSelectOK")
                        .addClass("btnGenericText")
                        .html("<b>Select</b>")
                    );

                    $("#skinSelectOK").click(function() {
                        viewer.toggleButtonState(true);
                        viewer.sd.load(viewer.activeId, viewer, viewer.toggleButtonState);
                        
                        viewer.loaded = true;
                        $('#selector').remove();
                        $('#darken').remove();
                        $('#selector2').remove();
                        $('#darken2').remove();
                        $(document.body).css("overflow", "auto");
                        viewer.searchResults = charData;
                    });
                    
                    var height = Math.max( document.body.scrollHeight, document.body.offsetHeight, 
                                       document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );  
                    $("#footer").css("top",height - $("#footer").height() - 20);
                }));
        }
    },
    loadFilter : function (filterType, container, color){
        if ($(container).length == 0){
            $("#searchContainer").append($("<div></div>")
                .attr("id",container.substring(1))
                .css({"width" : "100%", "margin-top" : "15px"}));
        }
        $(container).empty();
        var words = [];
        for (var i in viewer.searchResults){
            words.push(viewer.searchResults[i][filterType]);
        }
        var distinct = [];
        $.each(words, function(i, val){
            if ($.inArray(val, distinct) === -1) distinct.push(val);
        });
        for (var j in distinct){
            $(container).append($("<div>"+distinct[j]+"</div>")
                .addClass("btnGenericText")
                .css({"display" : "inline-block", "margin" : "0px 0px 5px 10px", "color" : color})
                .click(function(){
                    viewer.search($(this).html(), filterType);
                }));
        }
    },
    toggleButtonState : function(b){
        viewer.selectAnimation.prop("disabled", b);
        viewer.selectBG.prop("disabled", b);
        if (b){
            viewer.selectAnimation.css("color","gray");
            viewer.selectBG.css("color","gray");
            viewer.selectBG.attr("onclick","");
            viewer.selectShip.removeClass("q");
            viewer.selectShip.removeClass("spinetoolbar");
            viewer.selectShip.addClass("disabled-btn");
            viewer.selectShip.attr("onclick","");
        } else {
            viewer.selectAnimation.css("color","white");
            viewer.selectBG.css("color","white");
            viewer.selectBG.attr("onclick","onSelectBG()");
            viewer.selectShip.removeClass("disabled-btn");
            viewer.selectShip.addClass("spinetoolbar");
            viewer.selectShip.addClass("q");
            viewer.selectShip.attr("onclick","onSelectShip()");
        }
    },
    drawBG : function(url){
        var bgimg = PIXI.Sprite.fromImage(url);
        var h, w;
        h = viewer.app.view.height;
        w = viewer.app.view.width;
        bgimg.anchor.x = 0.5;
        bgimg.anchor.y = 0.5;
        bgimg.position.x = w/2;
        bgimg.position.y = h/2;
        if (viewer.app.stage.children[0] != null)
            viewer.app.stage.removeChildAt(0);
        viewer.app.stage.addChildAt(bgimg,0);
    }
};

function onChangeLog(){
    $(document.body).append($("<div></div>")
        .attr("id","darken")
        .addClass("darken")
        .css("top", window.pageYOffset + "px")
        .click(function(){
            $('#selector').remove();
            $('#darken').remove();
            $(document.body).css("overflow", "auto");
            viewer.searchResults = charData;
        }))
    .append($("<div></div>")
        .attr("id","selector")
        .addClass("selector")
        .css("top", (window.pageYOffset + (window.innerHeight * 0.05)) + "px")
        .css("padding", "2%"))
    .css("overflow", "hidden");
    $("#selector").append($("<table></table>")
        .addClass("wikitable")
        .append($("<tr></tr>")
            .append($("<td></td>")
                .css("background-color", "#24252D")
                .css("height", "30px")
                .css("padding-left", "8px")
                .html("<b>Changelog</b>")
            )
        )
        .append($("<tr></tr>")
            .append($("<td></td>")
                .attr("id", "chglog")
                .css("padding", "15px")
                .css("vertical-align","text-top")
            )
        )
    )

    var cb = function (response){
        for (i in response){
            var message = response[i].commit.message;
            var date = response[i].commit.committer.date;
            date = date.replace("T", " ");
            date = date.replace("Z", " UTC");

            $("#chglog").append($("<p></p>")
                .css("line-height", "0.8")
                .html(message+"<br>")
                .append($("<font></font>")
                    .css("font-size", "10px")
                    .css("color", "gray")
                    .html(date)
                )
            );
        }
    }

    var xobj = new XMLHttpRequest();
    xobj.open("GET", "https://api.github.com/repos/alg-wiki/AzurLaneSDViewer/commits?sha=gh-pages", true);
    xobj.setRequestHeader("Authorization", "token c44bb04d2275b3c1849b49f02d8c1b473c5b6864");
    //access token scope: <<no scope>>
    //Grants read-only access to public information (includes public user profile info, public repository info, and gists)
    xobj.onreadystatechange = function () {
          if (xobj.readyState == 4 && xobj.status == "200") {
            cb(JSON.parse(xobj.response));
          }
    };
    xobj.send(null); 
}

function onSelectShip(){
    $(document.body).append($("<div></div>")
        .attr("id","darken")
        .addClass("darken")
        .css("top", window.pageYOffset + "px")
        .click(function(){
            $('#selector').remove();
            $('#darken').remove();
            $(document.body).css("overflow", "auto");
            viewer.searchResults = charData;
        }))
    .append($("<div></div>")
        .attr("id","selector")
        .addClass("selector")
        .css("top", (window.pageYOffset + (window.innerHeight * 0.05)) + "px"))
    .css("overflow", "hidden");
    $("#selector").append($("<div></div>")
        .attr("id","searchContainer")
        .addClass("searchContainer")
        .css({"padding" : "15px"})
        .append($("<input>")
            .attr("id","searchField")
            .addClass("form-control")
            .css({"background-color": "#24252d", "color": "#ffffff", "display" : "inline-block"})
            .on("keyup", function(){
                var key = event.keyCode || event.charCode;
                viewer.search(null, null, key);
            })))
    .append($("<div></div>")
        .attr("id","resultContainer")
        .addClass("resultContainer"));
    viewer.loadFilter("type", "#searchType", "#ecd2fc");
    viewer.loadFilter("group", "#searchGroup", "#ccccff");
    viewer.loadResults(viewer.searchResults);
}

function onSelectBG(){
    var div = document.createElement('div');
    div.className = "darken";
    div.id = "darken";
    div.style.top = window.pageYOffset + "px";
    div.addEventListener("click", function(e) {
            document.body.removeChild(document.getElementById("selector"));
            document.body.removeChild(document.getElementById("darken"));
            document.body.style.overflow = "auto";
        }, false);
    document.body.appendChild(div);
    document.body.style.overflow = "hidden";
    var selector = document.createElement('div');
    selector.id = "selector";
    selector.className = "selector";
    selector.style.top = (window.pageYOffset + (window.innerHeight * 0.05)) + "px" ;
    document.body.appendChild(selector);
    for (var i = 0; i < backgroundData.length; i++){
        var img = document.createElement('div');
        img.className = "thumbbutton";
        img.style.backgroundImage = "url(../assets/bg/"+backgroundData[i]+")";
        img.style.backgroundSize = "500px auto";
        img.style.backgroundPosition = "50% 50%";
        img.id = backgroundData[i];
        img.addEventListener("click", function(e) {
            //document.getElementById("SdCanvas").style.backgroundImage = "url(../assets/bg/"+this.id+")";
            viewer.currentBG = "../assets/bg/"+this.id;
            viewer.drawBG(viewer.currentBG);
            document.body.removeChild(document.getElementById("selector"));
            document.body.removeChild(document.getElementById("darken"));
            document.body.style.overflow = "auto";
        }, false);
        document.getElementById("selector").appendChild(img);
    }
}

function check(a, b){
    for (var x in charData) {
        for (var i in charData[x].skin){
            $.ajax({
                url:'../'+a+charData[x].skin[i]+b,
                type:'HEAD',
                error: function()
                {
                    console.log(charData[x].skin[i]);
                },
                success: function()
                {
                    //file exists
                }
            });
        }
    }
}
