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
    'mousetrap',
    'bootbox',
    // semantic
    'semantic',
    // cello
    'cello_ui',
    'cello_gviz',
    // tmuse 'lib' (models, materials)
    'models',
    'materials',
    // jquery plugins
    'bootstrap_tagsinput'
], function($, _, Backbone, AutoComplete,  Mousetrap, bootbox, SemUI,Cello, cgviz, Models, Materials){
// Above we have passed in jQuery, Underscore and Backbone
// They will not be accessible in the global scope

    /**************************************************************************/
    /** The app itself
     * defines models, views, and actions binding all that !
    */

    function arrayMax(arr) {
      return arr.reduce(function (p, v) {
        return ( p > v ? p : v );
      });
    }
    function arrayMin(arr) {
      return arr.reduce(function (p, v) {
        return ( p < v ? p : v );
      });
    }

    // traduction des POS pour les vues
    var POS_MAPPING = {
        "A" : 'Adj.',
        "V" : 'V.',
        "N" : 'N.',
        "E" : 'Adv.',
    };

    /** View to manage WK definitions
    */
    var WkView = Backbone.View.extend({
        initialize: function(options){
            this.def_url = options.def_url;
            this.collection = new Backbone.Collection();
            this.listenTo(this.collection, 'reset', this.render );
            this.shortdesc = 'short';
            // wk dropdown
            var _this = this;
            $('#wkdef .dropdown')
              .dropdown({
                  on: "hover",
                onChange: function(value, text, $selectedItem) {
                  _this.shortdesc = $("#wkdef nav .menu a.item.active").data('desc') == "short";
                  _this.update_desc();
                  
                }
              })
            ;
        },

        update_desc:function(){
              if (this.shortdesc)
                $("#wkdef .wk-hiddable").hide()
              else
                $("#wkdef .wk-hiddable").show()
        },
        
        render: function(){
            var _this = this;
            $('#wkdef nav>a.item').remove();
            $('#wkdef .def-content').html("");
            
            var li = _.template("<a class='item <%=active%>' data-tab='<%=id%>'><%=lang%> <%=pos%> <%=form%></a>")
            var content = _.template("<div class='ui tab <%=active%>' data-tab='<%=id %>'><%=content %></div>");

            this.collection.each( function(e,i){
                var unit = _.extend({ active: i == 0 ? 'active' : "",
                                      id : 'tabpane'+i,
                                    } , e.attributes );
                $.ajax(
                    _this.def_url + unit.lang+"/" + unit.form + "?pos=" + unit.pos,
                    {
                        success : function(data){
                            unit.content = data.content;
                            $('#wkdef nav').append(li(unit));
                            $('#wkdef .def-content').append(content(unit));
                            $('#wkdef .item').tab({ context: $('#wkdef .def-content')});
                            _this.update_desc();
                        }
                    }
                );
            });
         },
     });

    /** Query input & completion **/
    var QueryView = Backbone.View.extend({
        //note: the template should have an input with class 'query_input'      
        template: _.template($('#query_form_tmpl').html() ),

        events: {
            'submit': 'submit',
            'drop input': 'drop',
            'click i.random': 'random'
        },

        initialize: function(attrs){
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
                "label": "",
                "placeholder": "Votre recherche ...",
                "submit": "rechercher !",
            }
            this.$el.html(this.template(data));

            /* tagsinput */
            var $input = $('#searchQueryInput', this.$el);
            $input.tagsinput({
              itemValue: function(model){return model},
              //itemText: function(model){return [model.get('lang'), model.get('pos'), model.get('form')].join(' ')},
              itemText: function(model){return [POS_MAPPING[model.get('pos')], model.get('form')].join(' ')},
              tagClass: function(model){ return 'ui label  pos-' + model.get('pos'); }
            });

            $input.on('itemRemoved', function(event){
                var item = event.item;
                _this.model.remove(item);
            });

            this.$input = $input;
            this.$tagsinput = $('.bootstrap-tagsinput input', this.$el);            

            /* completion */
            var CompletionItem = AutoComplete.ItemView.extend({
                // item completion view 
                template: _.template(""+
                         "<span class='label label-default pos-<%=pos%>'><%= text %></span> " +
                         "<span class=''><%= form %></span>"
                     ),

                render: function () {
                    var data = this.model.toJSON();
                    data.text = POS_MAPPING[data.pos];
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
               input : this.$tagsinput, // meta input created by tagsinput
               itemView: CompletionItem,               // item view
               queryParameter: "form",                 // options.data key for input
            });

            // append completion to the view
            $("#query_complete", this.$el).append(_this.querycomplete.render().$el);

            // random
            $("a", this.$el).click()
            
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
            
            view.$tagsinput.val("");
            view.$tagsinput.focus();
            return this;
        },

        random: function (event) {
            event.stopPropagation();
            event.preventDefault();
            $('input').blur();
            $('.page').click(); // should hide keyboard on android
            this.model.reset_random();
        },

        drop: function (event) {
            event.stopPropagation();
            event.preventDefault();
            var data = event.originalEvent.dataTransfer.getData("model");
            var ctrlKey = event.originalEvent.dataTransfer.getData("ctrlKey") == "true";
            
            var unit = new Models.TmuseQueryUnit();
            unit.set_from_str(data);
            if ( ctrlKey ) this.model.add(unit);
            else
                this.model.reset_from_models([unit]);
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

        // DEBUG
        DEBUG: false, // should be false by default else initialize can't change it

        initialize: function(options){
            var app = this;
            app.DEBUG = options.debug || app.DEBUG;
            
            this.root_url = options.root_url || "/";
            this.engine_url = options.engine_url;
            this.random_url = options.random_url;
            this.complete_url = options.complete_url;
            this.def_url = options.def_url;

            // manage debug
            Cello.DEBUG = app.DEBUG;
            // DEBUG: this un-activate the console,
            // console log  may cause performance issue on small devices
            if(!app.DEBUG){
                console.log = function() {}
            }
        },

        // create the models
        create_models: function(){
            var app = this;

            // create the engine
            app.models.cellist = new Cello.Engine({url: app.engine_url});

            // query specific tmuse (ici c'est une collection)
            // note: "query" should have an export_for_engine mth
            app.models.query = new Models.TmuseQueryUnits([], {random_url:app.random_url});
            
            // register the query model on the engine input "query"
            app.models.cellist.register_input("query", app.models.query);

            // completion
            CompleteCollection = AutoComplete.Collection.extend({
                url:app.complete_url,
                model: Backbone.Model.extend({
                    defaults: {
                        graph: "", lang: "", pos: "", form: ""
                    },
                }),
                update_data: function(data){
                    var units = app.models.query.models;
                    // prevents fetching completion with a different pos or lang
                    // if any item in query
                    if (units.length){
                        data.lang = units[0].get('lang')
                        data.pos = units[0].get('pos'),
                        data.graph = "jdm.asso"
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
            app.models.clustering = new Cello.Clustering({
                ClusterModel: Models.Cluster,
                color_saturation:71,
                color_value: 80,
            });

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
                className : 'clabel',
                template: _.template($('#cluster_item').html() ),
                events: {
                    "dragstart" : "drag",                    
                    "click a:has(> span) ": "click_to_graph",
                    "click a.button:has(> i.share)": "click_to_request",
                },

                click_to_request: function(event){
                    /* navigate */
                    event.preventDefault();
                    event.stopPropagation();                    
                    app.navigate_to_label(this.model);
                },
                
                click_to_graph: function(event){
                    app.views.gviz.model.vs.set_selected(null);
                    app.views.gviz.model.vs.set_selected(this.model);
                },

                drag: function (event) {
                    event.originalEvent.dataTransfer.setData('model', this.model.to_str());
                    event.originalEvent.dataTransfer.setData('ctrlKey', event.ctrlKey);
                },
                //RMQ: this computation may also be done directly in the template
                before_render: function(data){
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
                    "click a.draggable ": "click_to_graph",
                    "click a.button:has(> i.cube) ": "click_to_graph",
                    "click a.button:has(> i.share)": "click_to_request",
                    "mouseover": "mouseover",
                    "mouseout": "mouseout",
                    "dragstart" : "drag",
                    "addflag": "some_flags_changed",
                    "rmflag": "some_flags_changed",
                },

                initialize: function(options){
                    ItemView.__super__.initialize.apply(this);
                    this.listenTo(this.model, "rmflag:selected", this.flags_changed);
                    this.listenTo(this.model, "addflag:selected", this.some_flags_changed);
                },

                render: function() {
                    data = this.model.toJSON();
                    this.$el.html(this.template(data));
                    return this;
                },

                click_to_graph: function(event){
                    app.views.gviz.model.vs.set_selected(null);
                    app.views.gviz.model.vs.set_selected(this.model);
                },
                
                click_to_request: function(event){
                    app.navigate_to_label(this.model);
                },

                drag: function (event) {
                    event.originalEvent.dataTransfer.setData('model', this.model.to_str());
                    event.originalEvent.dataTransfer.setData('ctrlKey', event.ctrlKey);
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
                className: "ui selection list"
            }).render();


            /** Create view for graph */
            var graph = app.models.graph;

            var gviz = new Cello.gviz.ThreeViz({
                el: "#vz_threejs_main",
                model: graph,
                background_color: 0xEEEEEE,
                
                wnode_scale: function(vtx){
                    var v = (vtx.get('_size') * 14);
                    return 10 + this.user_vtx_size + v; 
                },

                materials: Materials,
                use_material_transitions: true,
                node_material_transition_delay: 200,
                edge_material_transition_delay: 300,

                show_text: true,
                
                adaptive_zoom: true,
                force_position_no_delay: false,
                debug: app.DEBUG,
                
            });
            
            gviz.on('reset', function(){

                this.camera.position.x = 500;
                this.camera.position.y = 600,
                this.camera.position.z = 600;

                this.camera.lookAt( new THREE.Vector3(0,0,0));
                tween = new TWEEN.Tween(this.camera.position)
                    .to({x:0,y:0,z:1500}, 1000)
                    .easing(TWEEN.Easing.Linear.None)
                    .start();
                                        
            });
            
            /* Events */                        

            gviz.on( 'intersectOff', function(event, node){
                graph.vs.set_intersected([]);
                app.views.gviz.request_animation();
            });
            // click events http://www.youtube.com/watch?v=tw1lEOUWmN8
            gviz.on( 'intersectOn:node', function(event, node){
                gviz.trigger('intersectOff');
                graph.vs.set_intersected(node !== null ? node : []);
            });
            
            gviz.on( 'intersectOn:edge', function(event, edge){
                app.views.gviz.request_animation();
            });    

            gviz.on( 'click:edge', function(event, edge){
                console.log( 'click:edge' , event);
            });

            gviz.on( 'click', function(event, obj){
                graph.vs.set_selected(obj);
                if (obj === null)
                    gviz.trigger('unselect_clusters');
                
            });
            
            gviz.on( 'click:node', function(event, node){
                graph.vs.set_selected(node);
                console.log("click", node, event);
            });

            /* Rendering looop */            
            gviz.enable().animate();

            app.views.gviz = gviz;

            // wk definitions
            app.views.wkdef = new WkView({def_url:app.def_url});
        },

        // helper: add app attributes to global scope
        // put cello and the app in global for debugging
        _add_to_global: function(){
            var app = this;
            window.Cello = Cello;
            window.app = app;
        },

        //### actions ###


        /** when a query is loading
         *
         * Update the rooter (url) and add waiting indicator
         */
        search_loading: function(kwargs, state){
            var app = this;
            // placeholder
            app.views.query.$tagsinput.attr('placeholder', "          ... Loading ...");
            app.views.query.$tagsinput.addClass('loading');
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
            app.views.query.$tagsinput.attr('placeholder', "Votre recherche");
            
            // collapse current graph viz
            if ( app.views.gviz ) {
                app.views.gviz.collapse(200);
            }

            app.update_models(response);
            
            app.router.navigate(response.results.query.uri);
            // force piwik (if any) to track the new 'page'
            Cello.utils.piwikTrackCurrentUrl();
            // linkify
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

            // computes node size [0,1]
            var neigh = app.models.graph.vs.map(function(vtx){
                //var v = 5 * Math.log(vtx.get("neighbors")); 
                return vtx.get('neighbors');
            });
            var mx = arrayMax(neigh);
            var mn = arrayMin(neigh);
            app.models.graph.vs.each(function(vtx){
                var nei = vtx.get('neighbors');
                vtx.set('_size', (nei-mn) / (mx-mn)) ;
            });
            
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
            app.models.clustering.clusters.each(function(cluster){
                cluster.listenTo(app.views.gviz, "unselect_clusters", function(){cluster.remove_flag('selected')})
            });

            // reset vertices collection !!! should be done after clustering reset 
            app.models.vertices.reset(app.models.graph.vs.models);

            // reset graph visualization
            app.views.gviz.reset();

            // edge color on node selection
            var graph = app.models.graph;
            graph.vs.each( function(node){

                app.views.gviz.listenTo(node, "addflag:intersected", function() {
                    
                    var nodes = node.neighbors();
                    nodes.push(node);
                    graph.vs.add_flag('mo-faded', _(graph.vs.models).difference(nodes));
                    graph.vs.add_flag('mo-adjacent', _(nodes).without(node));
                    
                    var edges = graph.incident(node);
                    graph.es.add_flag('es-bolder', edges);
                    graph.es.add_flag('es-mo-adjacent',  edges);
                    graph.es.add_flag('es-mo-faded', _.difference(graph.es.models, edges));

                    app.views.gviz.request_animation();
                });

                app.views.gviz.listenTo(node, "rmflag:intersected", function() {
                    graph.vs.remove_flag('mo-faded');
                    graph.vs.remove_flag('mo-adjacent');
                    
                    graph.es.remove_flag('es-mo-adjacent');
                    graph.es.remove_flag('es-mo-faded');
                    graph.es.remove_flag('es-bolder');
                       
                    app.views.gviz.request_animation();
                });
                
                app.views.gviz.listenTo(node, "addflag:selected", function() {

                    app.models.clustering.clusters.each(function(model){
                        model.remove_flag('selected');
                    });
                    
                    node.collection.remove_flag('cluster');
                    node.collection.remove_flag('selected', _(graph.vs.models).without(node));

                    var nodes = node.neighbors();
                    node.collection.add_flag('sel-faded', _(graph.vs.models).difference(nodes));
                    node.collection.add_flag('sel-adjacent', _(nodes).without(node));
                    
                    var edges = graph.incident(node);
                    graph.es.add_flag('es-bolder', edges);
                    graph.es.add_flag('es-sel-adjacent', edges);
                    graph.es.add_flag('es-sel-faded', _(graph.es.models).difference(edges));
                    
                    $("#maintabs a.tab-graph").click();
                    app.views.gviz.request_animation();
                });
                
                app.views.gviz.listenTo(node, "rmflag:selected", function() {
                    graph.vs.remove_flag('sel-faded');
                    graph.vs.remove_flag('sel-adjacent');
                    graph.es.remove_flag('es-sel-adjacent');
                    graph.es.remove_flag('es-sel-faded');
                    app.views.gviz.request_animation();
                });
                
                app.views.gviz.listenTo(node, "addflag:cluster", function() {
                    $("#maintabs a.tab-graph").click();
                    graph.vs.set_selected(null);                    
                    app.views.gviz.request_animation();
                });
            });
            
            // materials & images
            app.models.graph.vs.each(function(vtx){
                if(vtx.get('pzero'))
                    vtx.add_flag('target');
                else
                    vtx.add_flag("form");
                
            });

            /*  definition */
            app.views.wkdef.collection.reset(response.results.query.units);

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
            alert.addClass("reliureError");
            $("#maintabs").after(alert);
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

            // main function
        start: function(){
            var app = this;

            // initialize the app it self
            app.create_models();

            if(app.DEBUG){
                app._add_to_global();
            }

            // create views
            app.create_query_engine_views();
            app.create_results_views();

            // --- Binding the app ---
            _.bindAll(this, "engine_play_completed", "search_loading");
            this.listenTo(app.views.query, "submited", function(){
                if(app.models.query.validate()){
                    app.models.cellist.play();     //note: the cellist know query model
                }
            })
            
            // bind clusters
            //this.listenTo(app.models.clustering, 'change:selected', app.cluster_selected);

            // bind the engine
            // app events
            this.listenTo(app.models.cellist, 'engine:change', function(e){console.log('engine:change', e);});
            // bind query model, when play start
            this.listenTo(app.models.cellist, 'play:loading', app.search_loading);
            // when the search (play) is completed
            this.listenTo(app.models.cellist, 'play:complete', app.engine_play_completed);
            //when search failed
            this.listenTo(app.models.cellist, 'play:error', app.engine_play_error);


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

            app.models.cellist.fetch({ success: function(){
                // start history
                Backbone.history.start({pushState: true, root: app.root_url});
            }});

        },
    });
    return App;
});
