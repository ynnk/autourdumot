//Filename: app.js

/*
 requires boostrap-carousel & mousetrap
     http://timschlechter.github.io/bootstrap-tagsinput/examples/
     http://www.tutorialspoint.com/bootstrap/bootstrap_carousel_plugin.htm 
     http://craig.is/killing/mice
*/


define([
  // These are path alias that we configured in our main.js
    'jquery',
    'underscore',
    'backbone',
    'autocomplete',
    'bootstrap',
    'mousetrap',
    'bootbox',
    // cello
    'cello_ui',
    'cello_gviz',
    // tmuse 'lib' (models, materials)
    'models',
    'materials',
    // jquery plugins
    'bootstrap_tagsinput'
], function($, _, Backbone, AutoComplete, bootstrap, Mousetrap, bootbox, Cello, cgviz, Models, Materials){
// Above we have passed in jQuery, Underscore and Backbone
// They will not be accessible in the global scope

    // indicate if the app is in debug mode or not
    var DEBUG = true;
    Cello.DEBUG = DEBUG;

    //// DEBUG: this un activate the console,
    //// console log  may cause performance issue on small devices
    if(!DEBUG){
        console.log = function() {}
    }


    /**************************************************************************/
    /** The app itself
     * defines models, views, and actions binding all that !
    */
    var POS_MAPPING = {
        "A" : 'Adj.',
        "V" : 'V.',
        "N" : 'N.',
        "E" : 'Adv.',
    };

    /** Query input & completion **/
    var QueryView = Backbone.View.extend({
        //note: the template should have an input with class 'query_input'
        template: _.template($('#query_form_tmpl').html() ),

        events: {
            'submit': 'submit',
        },

        initialize: function(attr){
            var _this = this;
            _.bindAll(this, "render")

            /* model events */
            this.listenTo(this.model, 'add remove change reset', function(e){
                console.log("QueryView", e)
                _this.render();
                _this.submit();
            });

            /** Create the basic DOM elements **/
            /* form template */
            var data = {
                "label": "search :",
                "placeholder": "Enter a search ...",
                "submit": "search !",
            }
            this.$el.html(this.template(data));

            /* tagsinput */
            var $input = $('#searchQueryInput', this.$el);
            $input.tagsinput({
              itemValue: function(model){return model},
              //itemText: function(model){return [model.get('lang'), model.get('pos'), model.get('form')].join(' ')},
              itemText: function(model){return [POS_MAPPING[model.get('pos')], model.get('form')].join(' ')},
              tagClass: 'label label-primary'
            });

            $input.on('itemRemoved', function(event){
                var item = event.item;
                console.log("itemRemoved", item)
                _this.model.remove(item);
            });
            this.$input = $input;

            /* completion */
            var CompletionItem = AutoComplete.ItemView.extend({
                // item completion view 
                template: _.template(""+
                         //"<span class='label label-primary'><%= graph %></span> " +
                         //"<span class='label label-primary'><%= lang %></span> " +
                         "<span class='label label-default'><%= pos %></span> " +
                         "<span class=''><%= form %></span>"
                     ),

                render: function () {
                    var data = this.model.toJSON();
                    data.pos = POS_MAPPING[data.pos];
                    this.$el.html( this.template(data) );
                    return this;
                },

                select: function () {
                    console.log("completion select ", this.model.attributes)
                    _this.model.add(new Models.TmuseQueryUnit(this.model.attributes));
                    this.parent.hide();
                    return this;
                }
            });
            
            // completion view 
            _this.querycomplete = new AutoComplete.View({
               model : app.models.completion,          // CompleteCollection
               input : this.$input.tagsinput('input'), // meta input created by tagsinput
               itemView: CompletionItem,               // item view
               queryParameter: "form",                 // options.data key for input
            });

            // append completion to the view
            $("#query_complete", this.$el).append(_this.querycomplete.render().$el);
            return this.render();
        },

        render: function(){
            var view = this;
            // clear input 
            view.$input.tagsinput('removeAll');
            // add unit as tag
            view.model.each(function(unit){
                view.$input.tagsinput('add', unit);
            });
            
            view.$input.tagsinput('input').val("");
            view.$input.tagsinput('input').focus();
            return this;
        },
        
        // exec the search
        submit: function(event){
            /* 
             * Note: returns false to avoid HTML form submit
             */
            if (event){
                event.stopPropagation(); //not always necessary
                event.preventDefault(); // this will stop the event from further propagation and the submission will not be executed
            }
            // note: this is not necessary for Chrome, but needed for FF
            this.trigger("submited")
            return false;
        },
    });



    var App = Backbone.View.extend({
        // the main models, created in create_models()
        models: {},
        // the views, created in create_*_views()
        views: {},

        initialize: function(options){
            this.root_url = options.root_url || "/";
            this.engine_url = options.engine_url;
            this.complete_url = options.complete_url;
            this.def_url = options.def_url;
        },

        // create the models
        create_models: function(){
            var app = this;

            // create the engine
            app.models.cellist = new Cello.Engine({url: app.engine_url});

            // query specific tmuse (ici c'est une collection)
            // note: "query" should have an export_for_engine mth
            app.models.query = new Models.TmuseQueryUnits();
            
            // register the query model on the engine input "query"
            app.models.cellist.register_input("query", app.models.query);

            //  completion
            CompleteCollection = AutoComplete.Collection.extend({
                url:app.complete_url,
                model: Backbone.Model.extend({
                        defaults : {
                            graph: "", lang: "", pos: "", form: ""
                        },
                    }),
                update_data: function(data){
                    var units = app.models.query.models;
                    // prevents fetching completion with a different pos or lang
                    // if any item in query
                    if (units.length){
                        data.lang = units[0].get('lang')
                        data.pos = units[0].get('pos')
                    }
                    return data;
                },
            });

            app.models.completion = new CompleteCollection({});

            // --- Graph model ---
            app.models.graph = new Cello.Graph({
                            vertex_model: Models.Vertex,
                            edge_model: Models.Edge,
                }) //warn: it is updated when result comes

            // clustering
            app.models.clustering = new Cello.Clustering({ClusterModel: Models.Cluster, color_saturation:50});

            // prox list (proxy to app.models.graph.vs)
            app.models.vertices = new Cello.DocList([], {sort_key:'label'});
       },


        /** Create views for query (and engine)
         *
         * home: if true the app is setted with search input in middle of the page
         */ 
        create_query_engine_views: function(){
            var app = this;
            var searchdiv = '#query_form';
            
            app.views.query = new QueryView({
                model: app.models.query,
                el: $(searchdiv),
            }).render();
            $(searchdiv).show();
            //Note this view submited event is binded in the start
        },


        /** Create documents list views
         */
        create_results_views: function(){

            var app = this;

            var ClusterVtx = Cello.ui.clustering.ClusterMemberView.extend({
                //template: _.template($('#ClusterLabel').html().trim()),
                className : 'clabel',
                events: {
                    "click": "clicked",
                },

                /* Click sur le label, */
                clicked: function(event){
                    /* navigate */
                    event.preventDefault();
                    event.stopPropagation();

                    // 'this.model' is a label not a vertex !
                    /* select vertex */
                    var vertices = app.models.graph.select_vertices({label:this.model.label});
                    var vertex = vertices[0];
                    
                    /* navigate */
                    app.navigate_to_label(this.model.label);
                },

                //RMQ: this computation may also be done directly in the template
                before_render: function(data){
                    //console.log(data.label, data.score)
                    data.size = Math.max(10,data.score * 26.);
                    return data
                },
            });

            // vertices list
            var ClusterVerticesView = Cello.ui.list.CollectionView.extend({
                className: "vs_list",
                ChildView: ClusterVtx, 
            });

            // view over a cluster
            var ClusterView = Cello.ui.clustering.ClusterView.extend({
                MembersViews: {'vs' : ClusterVerticesView }
            });

            /** Create views for clustering */
            app.views.clustering = new Cello.ui.list.CollectionView({
                collection: app.models.clustering.clusters,
                ChildView: ClusterView,
                el: $("#clustering_items ul"),
            }).render();

            // vertex sorted by proxemy
            
            var ItemView = Cello.ui.doclist.DocView.extend({
                template: _.template($("#ListLabel").html()),
                events:{
                    "click": "clicked",
                    "mouseover": "mouseover",
                    "mouseout": "mouseout",
                    "addflag": "some_flags_changed",
                    "rmflag": "some_flags_changed",
                },

                 initialize: function(options){
                    // super call
                    ItemView.__super__.initialize.apply(this);
                    // override
                    this.listenTo(this.model, "rmflag:selected", this.flags_changed);
                    this.listenTo(this.model, "addflag:selected", this.some_flags_changed);
                },

                render: function() {
                    data = this.model.toJSON();
                    this.$el.html(this.template(data));
                    return this;
                },

                /* Click sur le label, */
                clicked: function(event){
                    console.log("item clicked", this.model)
                    app.navigate_to_label(this.model);
                },

                mouseover: function(){
                    app.models.graph.vs.set_intersected(this.model);
                },

                mouseout: function(){
                    app.models.graph.vs.set_intersected(null);
                },
                some_flags_changed: function(){
                    this.flags_changed();
                    this.scroll_to();
                },

            });


            /** Create view for liste */
            app.views.proxemy = new Cello.ui.list.CollectionView({
                collection : app.models.vertices,
                ChildView: ItemView,
                el: $("#proxemy_items ul"),
            }).render();


            /** Create view for graph */
            var gviz = new Cello.gviz.ThreeViz({
                el: "#vz_threejs_main",
                model: app.models.graph,
                background_color: 0xEEEEEE,
                wnode_scale: function(vtx){
                    return 8 + vtx.get("neighbors") / 8.;
                },
                force_position_no_delay: false,
                materials: Materials
                
            });
            //var materials = JSON.parse(Materials);
            
            var graph = app.models.graph;
            
            /* Events */
            
            // intersect events
            gviz.on( 'intersectOn:node', function(vertex, mouse){
                gviz.model.vs.set_intersected(vertex);
            });
            
            //gviz.on( 'intersectOn:edge', function(edge, mouse){
                //gviz.model.es.set_intersected(edge);
            //});
            
            gviz.on( 'intersectOff', function(obj, mouse){
                gviz.model.es.set_intersected(null);
                gviz.model.vs.set_intersected(null);
                console.log("intersect",obj)
                gviz.request_animation();
            } );

            // click eventshttp://www.youtube.com/watch?v=tw1lEOUWmN8
            gviz.on( 'click:node', function(node, event){
                // multiple selection
                //if ( event.ctrlKey )
                    //gviz.model.vs.add_selected(obj !== null ? obj : []);
                //else // single
                gviz.model.vs.set_selected(node !== null ? node : []);

                var nodes = node.neighbors();
                graph.vs.add_flag('faded', _.difference(graph.vs.models, nodes));

                var edges = graph.incident(node);
                graph.es.add_flag('faded', _.difference(graph.es.models, edges));
                console.log( 'click:node' , event);
                
            });

            gviz.on( 'click:edge', function(obj, event){
                //alert(JSON.stringify( event));
                console.log( 'click:edge' , event);
            });
            
            gviz.on( 'click', function(obj, event){
                if( obj === null ){
                    gviz.model.vs.set_selected(null);
                    graph.vs.remove_flag('faded');
                    graph.es.remove_flag('faded');
                }
                console.log("click", obj, event);
                gviz.request_animation();
            });
            
            /* Rendering looop */            
            gviz.enable().animate();

            app.views.gviz = gviz;
        },

        // helper: add app attributes to global scope
        // put cello and the app in global for debugging
        _add_to_global: function(){
            var app = this;
            window.Cello = Cello;
            window.app = app;
        },

        //### actions ###

        /** When a cluster is selected
         *
         * if one (or more) cluster is selected:
         *  * add a tag 'cluster_active' on all document of selected cluster
         *  * add a tag 'cluster_hidden' on all other documents
         *
         * if no cluster are selected
         *  * remove this two tags from documents
         */
        cluster_selected: function(){
            var app = this;
            // // get selected clusters
            var selected = app.models.clustering.selected;

            if(selected.length == 0){
                // remove all flags
                app.models.graph.vs.each( function(vertex){
                    vertex.remove_flag('faded');
                });
            } else {
                // fade/unfade vertices in clusters
                var vids = {}
                _.each(selected, function(cluster){
                    _.each(cluster.vids, function(vid){
                        vids[vid] = true;
                    })
                });
                app.models.graph.vs.each( function(vertex){
                    if (_.has(vids, vertex.id)){
                        vertex.remove_flag('faded');
                    }
                    else {
                        vertex.add_flag('faded');
                    }
                });
                app.models.graph.es.each( function(edge){
                    if (_.has(vids, edge.source.id) || _.has(vids, edge.target.id)){
                        edge.remove_flag('faded');
                    } else {
                        edge.add_flag('faded');
                    }
                });
            }
        },

        /** when a query is loading
         *
         * Update the rooter (url) and add waiting indicator
         */
        search_loading: function(kwargs, state){
            var app = this;

            //start waiting
            $("#loading-indicator").show(0);
            $("#engine").hide();
            
            // placeholder
            app.views.query.$input.tagsinput('input').attr('placeholder', "          ... Loading ...");
            
            // force piwik (if any) to track the new 'page'
            //Cello.utils.piwikTrackCurrentUrl();
        },

        /** when a search response arrive (in success)
         */
        engine_play_completed: function(response, args, state){
            var app = this;
            if(app.DEBUG){
                console.log("play:complete", 'args', args, 'state', state);
                app.response = response;    // juste pour le debug
            }
            //stop waiting
            $("#loading-indicator").hide(0);
            app.views.query.$input.tagsinput('input').attr('placeholder', "Search");
            
            // collapse current graph viz
            if ( app.views.gviz ) {
                app.views.gviz.collapse(200);
            }

            app.update_models(response);
            app.router.navigate(response.results.query.uri);
        },

        /* callback when new data arrived */
        update_models: function(response){
            // parse and reset graph
            app.models.graph.reset(response.results.graph);

            // apply layout
            var coords = response.results.layout.coords;
            for (var i in coords){
                app.models.graph.vs.get(i).set("coords", coords[i], {silent:true});
            }

            // reset vertices collection
            app.models.vertices.reset(app.models.graph.vs.models);

            // reset clustering
            app.models.clustering.reset(
                response.results.clusters,
                {
                    members: {
                        vs:{
                            source: app.models.graph.vs,
                            id_field: 'vids' 
                        }
                    }
                }
            );

            // default color does not depend on visible panel
            app.models.graph.vs.copy_attr('cl_color', 'color',{silent:true});

            // reset graph visualization
            app.views.gviz.reset();

            // edge color on node selection
            var graph = app.models.graph;
            graph.vs.each( function(node){
                
                app.views.gviz.listenTo(node, "rmflag:selected", function() {
                    _.each(graph.incident(node), function(edge){
                        edge.remove_flag("selected");
                    });            
                    app.views.gviz.request_animation();
                });

                app.views.gviz.listenTo(node, "addflag:selected", function() {
                    _.each(graph.incident(node), function(edge){
                        edge.add_flag('selected');
                    });
                    app.views.gviz.request_animation();
                });
            });
            
            // materials & images
            app.models.graph.vs.each(function(vtx){
                if(vtx.get('pzero'))
                    vtx.add_flag('target');
                else
                    vtx.add_flag("form");
                vtx.label = function(){ return this.get('form') };
            });

            /*  definition */
            // TODO: create a proper view/model if this become bigger...
            // clear nav & .def
            $('#wkdef .nav').html("");
            $('#wkdef .tab-content').html("");

            li = _.template("<li class='<%=active%>'><a href='#<%=id%>' data-toggle='tab'><%=lang%> <%=pos%> <%=form%></a></li>")
            
            _.each(response.results.query.units, function(e,i){
                var unit = _.extend({ active: i == 0 ? 'active' : "", id : 'tabpane'+i }, e );
                $.ajax(
                    app.def_url + unit.lang+"/" + unit.form + "?pos=" + unit.pos,
                    {
                        success : function(data){
                            $('#wkdef .nav').append(li(unit));
                            $('#wkdef .tab-content').append("<div class='tab-pane "+ unit.active +"' id='"+unit.id+"'>" + data.content + "</div>");
                        }
                    }
                );
            });
            $('#tabs').tab();
        },

        /** when the search failed
         */
        engine_play_error: function(response, xhr){
            var app = this;
            if(app.DEBUG){
                console.log("play:error", 'response', response);
                app.response = response;    // juste pour le debug
                app.xhr = xhr;
            }

            //stop waiting
            $("#loading-indicator").hide(0);

            var text;

            if(!_.isEmpty(response)){
                // There is a cello response
                // so we can get the error messages
                text = response.meta.errors.join("<br />");
            } else {
                // HTTP error, just map the anwser
                text = $(xhr.responseText);
                // HACK:
                $("body").css("margin", "0"); //note: the Flask debug has some css on body that fucked the layout
            }

            var alert = Cello.ui.getAlert(text);
            $("body").prepend(alert);
        },


        /** Navigate (=play engine) to a vertex by giving it exact label
        */
        navigate_to_label: function(model){
            var app = this;
            //XXX: rename label to ??
            if (_.isString(model) )
                app.models.query.reset_from_str(model) ;
            else
                app.models.query.reset_from_models(model) ;
        },

        showAbout: function(){
            var msg = _.template($("#about_tmpl").text());
            bootbox.dialog({
              title: "A propos de TMuse",
              message: msg,
              onEscape: function() {},
              buttons: {
                main: {
                  label: "OK",
                  className: "btn-primary",
                  callback: function() {}
                }
              }
            });
        },

        // main function
        start: function(){
            var app = this;
            app.DEBUG = DEBUG;

            // get the root url from the template
            //// note: this is usefull to have the app instaled in unknow 'suburl'
            //app.root_url = $("#page").attr("data-root-url");

            // initialise the app it self
            app.create_models();

            ///// DEBUG: this add the app to global (guardian_app)
            if(app.DEBUG){
                app._add_to_global();
            }

            // create views
            app.create_query_engine_views();
            app.create_results_views();

            // --- Binding the app ---
            _.bindAll(this, "engine_play_completed", "cluster_selected", "search_loading");
            this.listenTo(app.views.query, "submited", function(){
                if(app.models.query.validate()){
                    app.models.cellist.play();     //note: the cellist know query model
                }
            })
            
            // bind clusters
            this.listenTo(app.models.clustering, 'change:selected', app.cluster_selected);

            // bind the engine
            // app events
            this.listenTo(app.models.cellist, 'engine:change', function(e){console.log('engine:change', e);});
            // bind query model, when play start
            this.listenTo(app.models.cellist, 'play:loading', app.search_loading);
            // when the search (play) is completed
            this.listenTo(app.models.cellist, 'play:complete', app.engine_play_completed);
            //when search failed
            this.listenTo(app.models.cellist, 'play:error', app.engine_play_error);

            /* keyboard shortcuts */

            Mousetrap.bind(['?', ','], function(){
                $("#query_form div.bootstrap-tagsinput input").focus().select();
                return false;
            });

            // engine
            Mousetrap.bind('p,P'.split(','), function(){
                $("a.engine_on_off").click();
            });
            
            // arrows
            Mousetrap.bind('right', function(){
                $("#myCarousel").carousel("next");
            });
            Mousetrap.bind('left', function(){
                $("#myCarousel").carousel("prev");
            });

            // direct slide access
            var kevents = { 'g,G' : 0, 'c,C':1, 'l,L':2, 'd,D':3 }
            _.each(kevents , function(v,k){
                console.log(k,v)
                Mousetrap.bind(k.split(','), function(){
                    $("#myCarousel").carousel(v)
                });
            });

            /* resize window event */
            var min_height = 250;
            
            var _window_resized = function(){
                var win = $(this); //this = window
                size =  $(window).height()-88;
                size = size < min_height ? min_height : size;
                $("#myCarousel .item").height(size);
                app.views.gviz.resize_rendering()
            }

            // bug refresh graph viz
            $('#myCarousel').on('slid.bs.carousel',function(){
                setTimeout(150,_window_resized);
                console.log('carousel resize')
            });
            $(window).on('resize', function(){
                _window_resized();
            });

            // about menu
            $("a.about").on('click', function(){
                app.showAbout();
            })

            // Router
            var AppRouter = Backbone.Router.extend({
                routes: {
                    '': 'index',
                    ':query': 'search',
                },

                initialize: function() {
                    console.log('<router init>');
                },

                index: function() {
                    console.log('<router> root /');
                },

                search: function( query){
                    console.log("<router> search start");
                    console.log("navigate_to_label", query);
                    app.navigate_to_label(query);
                }
            });

            // create the rooter
            app.router = new AppRouter();
            // Everything is now in place...

            console.log(app.models.cellist.url, {url: app.engine_url})
            app.models.cellist.fetch({ success: function(){
                // start history
                Backbone.history.start({pushState: true, root: app.root_url});
            }});

            _window_resized();

        },
    });
    return App;
    // What we return here will be used by other modules
});
