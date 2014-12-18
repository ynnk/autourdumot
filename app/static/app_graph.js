//Filename: app.js

define([
  // These are path alias that we configured in our main.js
    'jquery',
    'underscore',
    'backbone',
    'autocomplete',
    'bootstrap',
    'mousetrap',
    // cello
    'cello_core',
    'cello_ui',  // user interface
    'cello_gviz' // graph visualisation
], function($, _, Backbone, AutoComplete, bootstrap, Mousetrap, Cello){
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
    
    var CompletionItem = AutoComplete.ItemView.extend({
        template: _.template("<a href='#' class='lang'> <%= lang %> <%= pos %> <%= form %></a>"),
        
        render: function () {
            //this.$el.html( this.template(this.model.attributes) );
            
            var attrs = this.model.attributes;
            var html = _.map( ['lang', 'pos','form' ], function(e){
                return "<span class='"+e+"'>"+attrs[e]+"</span>";
            }).join(" ");
            
            this.$el.html(html);
            
            //console.log("log", html);
            
            return this;
        },

        select: function () {
            this.parent.hide().select(this.model);
            return false;
        }

    });
    
    var CompleteCollection = Backbone.Collection.extend({
        url : "ajax_complete",
        model : Backbone.Model.extend({
            defaults : {
                graph: "",
                lang: "",
                pos: "",
                form: ""
            },
        }),
        parse: function(data){
            return data.complete;
        }    
    });


    var TmuseQueryUnit = Backbone.Model.extend({
        defaults: {
            graph: null,    // name of the graph
            lang: null,
            pos: null,
            form: null,
            boost: 1,
            // surface attr
            valid: false,
        },

        initialize: function(){
            // validate on each change
            this.on("change:graph change:lang change:pos change:form", this.validate);
        },

        /* Set the Query unit from a raw string, 
         * ex 
         *  * "DS_V.fr.V.manger"
         *  * "fr.V.manger"
         *  * "V.jouer"
         *  * "rire"
        */
        //TODO: add boost parsing ("fr.V.manger:50")
        set_from_str: function(query_str){
            var qsplit = query_str.trim().split(".");
            data = {}
            data.form = qsplit[qsplit.length-1];
            if(qsplit.length >= 2){
                data.pos = qsplit[qsplit.length-2];
            }
            if(qsplit.length >= 3){
                data.lang = qsplit[qsplit.length-3];
            }
            if(qsplit.length >= 4){
                data.graph = qsplit[qsplit.length-4];
            }
            this.set(data);
        },

        to_string: function(){
            var str = [];
            //TODO: Cello.get !
            //TODO loop on graph, lang, pos
            if(!_.isNull(this.get("graph"))){
                str.push(this.get("graph"));
            }
            if(!_.isNull(this.get("lang"))){
                str.push(this.get("lang"));
            }
            if(!_.isNull(this.get("pos"))){
                str.push(this.get("pos"));
            }
            str.push(this.get("form"));
            str = str.join(".")
            if(this.get("boost") != 1.){
                str = str + ":" + this.get("boost");
            }
            return str;
        },

        /* Ajax call to check if this query unit exist (and so is valid)
        */
        validate: function() {
            //TODO
        },
    })

    var TmuseQueryUnits = Backbone.Collection.extend({
        model: TmuseQueryUnit,

        /* Reset the QueryUnit collection from a raw string, ex "fr.V.manger;fr.V.boufer"
        */
        reset_from_str: function(query_str){
            var data = [];
            var qsplit = query_str.split(";");
            _.each(qsplit, function(qstr){
                var query_elem = new TmuseQueryUnit();
                query_elem.set_from_str(qstr);
                data.push(query_elem);
            });
            this.reset(data);
        },

        to_string: function(){
            return this.models.map(function(qunit){ return qunit.to_string() }).join(", ");
        },

        validate: function(){
            //TODO
        },

        export_for_engine: function(){
            return this.toJSON();
        },
    });


    //XXX: A REPRENDRE...
    var QueryView = Backbone.View.extend({
        //note: the template should have an input with class 'query_input'
        template: Cello.ui.getTemplate(Cello.ui.templates.basic, '#query_form_tmpl'),

        events: {
            'submit': 'submit',
            'keypress':'keypress'
            //'click .query_randomq': 'randomq',
        },

        initialize: function(attr){
            _.bindAll(this, "update_query", "update_loaded")
            // re-render when the model change
            this.listenTo(this.model, 'change:query', this.update_query);
            this.listenTo(this.model, 'change:loaded', this.update_loaded);
            // getter for the input field

            Cello.get(this, "$input", function(){
                var inputs = this.$('input.query_input', this.$el);
                return this.$(inputs[0])
            });
            
            console.log(this.$input)
            
            // autocomplete
           
            return this;
        },

        // update query value in the input
        update_query: function(){
            this.$input.val(this.model.to_string());
        },

        // update query value in the input
        update_loaded: function(){
            console.log("loaded", this.model.loaded);
            if(this.model.loaded){
                this.$el.find("[type='submit'] span.glyphicon").remove();
            } else {
                var play_icon = $("<span class='glyphicon glyphicon-play'></span>")
                this.$el.find("[type='submit']").prepend(" ").prepend(play_icon);
            }
        },

        render: function(){
            var data = {
                "label": "search :",
                "placeholder": "Enter a search ...",
                "submit": "search !",
            }
            // setup the template
            this.$el.html(this.template(data));
            // update the query input
            this.update_query();
            this.update_loaded();
            
            return this;
        },

        /** Return the string of the typed query
         */
        query_str: function(){
            return this.$input.val();
        },

        keypress: function(event){
            //q = this.query_str();
            //$.ajax('complete/'+ q, {
               //success: function(data){
                    //console.log(data)
                //}, 
            //});
            //this.complete.refresh()
        },
        
        // exec the search
        submit: function(event){
            /* 
             * Note: returns false to avoid HTML form submit
             */
            event.preventDefault(); // this will stop the event from further propagation and the submission will not be executed
            // note: this is not necessary for Chrome, but needed for FF
            this.model.set_form(this.query_str())
            this.model.run_search();

            event.stopPropagation(); //not always necessary
            return false;
        },
    });



    var App = Backbone.View.extend({
        // the main models, created in create_models()
        models: {},
        // the views, created in create_*_views()
        views: {},

        initialize: function(options){
            this.root_url = options.root_url || "/"
        },

        // create the models
        create_models: function(){
            var app = this;

            // create the engine
            app.models.cellist = new Cello.Engine({url: app.root_url+"api"});
            //NOTE: the url is from root, issue comming if "api" entry point is not at root

            // query specific tmuse (ici c'est une collection)
            // note: "query" should have an export_for_engine mth
            app.models.query = new TmuseQueryUnits();
            app.models.query.reset_from_str("fr.V.manger");
            
            app.models.completion = new CompleteCollection();
            
            // register the query model on the engine input "query"
            app.models.cellist.register_input("query", app.models.query);

            // --- Graph model ---
            app.models.graph = new Cello.Graph({}) //warn: it is updated when result comes

            // --- Clustering model ---
            // Clustering model and view
            app.models.clustering = new Cello.Clustering({color_saturation:50});
            app.models.vertices = new Cello.DocList({sort_key:'label'});
       },

     // change the views to search results
        open_results_view: function(force){
            var app = this;
            if(!app.search_results || force){
                app.search_results = true;
                app.create_results_views();
            }
        },

        // change the views to home page
        open_home_view: function(force){
            var app = this;
            if(app.search_results || force){
                app.search_results = false;
                app.create_query_engine_views(true);
            }
        },


        /** Create views for query and engine
         *
         * home: if true the app is setted with search input in middle of the page
         */
        create_query_engine_views: function(home){
            var app = this;
            var searchdiv = '#query_form';
            app.views.query = new QueryView({
                model: app.models.query,
                el: $(searchdiv),
            }).render();
            $(searchdiv).show();

            // commpletion
            app.views.querycomplete = new AutoComplete.View({
               model : app.models.completion, 
               input : app.views.query.$input,
               itemView: CompletionItem
            });
                       
            $("#query_complete", app.views.query.$el).append(app.views.querycomplete.render().$el)

            // Configuration view for Cello engine
            app.views.keb = new Cello.ui.engine.Keb({
                model:app.models.cellist,
                el:"#engine"
            }).render();
            $("#engine").hide(); // hided by default

            // toggle for  #engine view
            $(searchdiv).find("form")
                .append("<a href='#' class='engine_on_off glyphicon glyphicon-cog'></a>")
            // add vue to toggle
            $("a.engine_on_off", searchdiv).click(function(event){
                event.preventDefault();
                $("#engine").toggle();
            });
        },


        /**
         *   Create documents list views
         */
        create_results_views: function(){

            var app = this;

            /** Create views for clustering */

            // label view
            // Note: the inheritage is not absolutely needed here, except for label overriding.
            // however if one want to add clustom events on each label it should
            // do that, so as documentation/exemple it is usefull the 'extend'.

            var ClusterLabel = Cello.ui.clustering.LabelView.extend({
                template: _.template($('#ClusterLabel').html().trim()),

                events: {
                    "click": "clicked",
                },

                /* Click sur le label, */
                clicked: function(event){
                    /* navigate */
                    event.preventDefault();
                    event.stopPropagation();

                    /* navigate */
                    //app.navigate_to_label(this.model.label);

                    /* select vertex */
                    // 'this.model' is a label not a vertex !
                    var vertices = app.models.graph.select_vertices({label:this.model.label});
                    var vertex = vertices[0];
                    app.navigate_to_label(this.model.label);
                },

                //RMQ: this computation may also be done directly in the template
                before_render: function(data){
                    //console.log(data.label, data.score)
                    data.size = Math.max(10,data.score * 26.);
                    return data
                },
            });

            // view over a cluster
            var ClusterItem = Cello.ui.clustering.ClusterItem.extend({
                tagName: 'li',
                LabelView: ClusterLabel,
            });

            // Cluster (label lists) view
            // Note: the list of cluster is just a classical ListView
            app.views.clustering = new Cello.ui.list.ListView({
                model: app.models.clustering,
                ItemView: ClusterItem,
                el: $("#clustering_items"),
            }).render();

            // when #clustering_items is "show" change graph colors
            $('#clustering_items').on('show.bs.collapse', function () {
                app.models.graph.vs.copy_attr('cl_color', 'color',{silent:true});
                //app.views.gviz.update();
            });

            // vertex sorted by proxemy
            var ItemView = Cello.ui.doclist.DocItemView.extend({
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
                    app.navigate_to_label(this.model.label);
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

            app.views.proxemy = new Cello.ui.list.ListView({
                model : app.models.vertices,
                ItemView: ItemView,
                el: $("#proxemy_items"),
            }).render();



            /** Create view for graph */

            var gviz = new Cello.gviz.ThreeViz({
                el: "#vz_threejs_main",
                model: app.models.graph,
                background_color: 0xEEEEEE,
                wnode_scale: function(vtx){
                    return 10 + vtx.get("neighbors") / 8.;
                },
                force_position_no_delay: true
            });
            
            /* Materials 
             * rendering edges & vertices materials 
             */

            gviz.add_material( 'node', '.form', {
                    'shape': 'circle',
                    'scale':1,
                    //'shape': 'triangle',
                    'lineWidth' : 0.01,
                    'fontScale'  :  0.2,
                    'fontFillStyle'  : '#333',  //#366633',           
                    'fontStrokeStyle'  : '#333',
                    'textPaddingY'  : -10
            } );
            gviz.add_material( 'node', '.form:intersected', {
                    'shape': 'square',
                    'scale':1,
                    'fontScale'  :  0.2,
            } );
            gviz.add_material( 'node', '.form:selected', {
                    'shape': 'square',
                    'scale':1,
                    'strokeStyle': "gradient:#1D1D1D",
                    'fontScale'  :  0.3,
            } );

            /* Events */
            
            // intersect events
            gviz.on( 'intersect:node', function(vertex, mouse){
                    gviz.model.vs.set_intersected(vertex);
            });
            
            gviz.on( 'intersect:edge', function(edge, mouse){
                gviz.model.es.set_intersected(edge);
            });
            gviz.on( 'intersect', function(obj, mouse){
                if ( obj === null ){
                    gviz.model.es.set_intersected(null);
                    gviz.model.vs.set_intersected(null);
                }
                //console.log("intersect",obj)
                gviz.request_animation();
            } );

            // click events
            gviz.on( 'click:node', function(obj, event){
                // multiple selection
                if ( event.ctrlKey )
                    gviz.model.vs.add_selected(obj !== null ? obj : []);
                else // single 
                    gviz.model.vs.set_selected(obj !== null ? obj : []);
            });

            gviz.on( 'click:edge', function(obj, event){
                //alert(JSON.stringify( event));
                console.log( event);
            });
            
            gviz.on( 'click', function(obj, event){
                if( obj === null )
                    gviz.model.vs.set_selected(null);
                console.log( obj, event);
                gviz.request_animation();
            });
            
            /* Rendering */
            
            // gviz rendering loop
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

        /** Navigate (=play engine) to a vertex by giving it exact label
        */
        navigate_to_label: function(label){
            var app = this;
            //XXX: rename label to ??
            app.models.query.reset_from_str(label) ;
            app.models.cellist.play();

        },

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

            // force piwik (if any) to track the new 'page'
            Cello.utils.piwikTrackCurrentUrl();

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
            
            // collapse current graph viz
            if ( app.views.gviz ) {
                app.views.gviz.collapse(200);
            }

            app.open_results_view();
            app.update_models(response);
            //app.router.navigate(response.results.query.form);
        },

        update_models: function(response){

            // parse graph
            app.models.graph.reset(response.results.graph);

            // apply layout
            var coords = response.results.layout.coords;
            for (var i in coords){
                app.models.graph.vs.get(i).set("coords", coords[i], {silent:true});
            }

            // reset clustering
            app.models.clustering.reset(response.results.clusters);

            // set cluster colors on vertices
            _.map(app.models.graph.vs.select({}), function(model, i, list ){
                model.set('default_color', model.get('color'))
                var cid = app.models.clustering.membership[model.id]
                model.set('cl_color', app.models.clustering.cluster(cid[0]).color, {silent:true});
            });
            

            // FIXME :
            // default color does not depend on visible panel
            app.models.graph.vs.copy_attr('cl_color', 'color',{silent:true});

            // reset graph visualization
            app.views.gviz.reset();

            // reset proxemy view
            app.models.vertices.reset(app.models.graph.vs.models);
            
            // edge color on node selection
            app.models.graph.vs.each( function(node){
                app.views.gviz.listenTo(node, "rmflag:selected", function() {
                    _.each(node.neighbors(), function(edge){
                        edge.remove_flag("selected");
                    });            
                    app.views.gviz.request_animation();
                });

                app.views.gviz.listenTo(node, "addflag:selected", function() {
                    _.each(node.neighbors(), function(edge){
                        edge.add_flag('selected');
                    });
                    app.views.gviz.request_animation();
                });
            });
            
            
            // materials & images
            app.models.graph.vs.each(function(vtx){
                    vtx.add_flag("form");
                    vtx.label = function(){ return this.get('label') };
            });
            
            // definition
            var lang = response.results.query.lang;
            var form = response.results.query.form;
            $.ajax( "def/"+lang+"/"+form, {
                    success : function(data){
                        $('#wkdef').html(data.content)
                    }
                });
            
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
            app._add_to_global();

            app.has_search_results = false // indicate that the search result view is not open
            app.open_home_view(true);

            // --- Binding the app ---
            _.bindAll(this, "engine_play_completed", "cluster_selected", "search_loading");
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

            // keyboard shortcuts
            Mousetrap.bind('?', function(){
                $("#searchQueryInput").focus();
                return false;
            });
            
            var kevents = { 'g,G' : 0, 'c,C':1, 'l,L':2, 'd,D':3 }
            _.each(kevents , function(v,k){
                console.log(k,v)
                Mousetrap.bind(k.split(','), function(){
                    $("#myCarousel").carousel(v)
                });
            });



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
                    app.open_home_view();
                    app.navigate_to_label("causer");
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
    // What we return here will be used by other modules
});
