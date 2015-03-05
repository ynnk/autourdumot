/* Models */

define(['underscore','backbone', 'cello_core'],    function(_,Backbone, Cello) {
  
    var Models = {};

    /* Query */
    Models.TmuseQueryUnit = Backbone.Model.extend({
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
            console.log(data)
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
    });

    Models.TmuseQueryUnits = Backbone.Collection.extend({
        model: Models.TmuseQueryUnit,

        initialize: function(models, options){
            this.random_url = options.random_url;
        },

        /* Reset the QueryUnit collection from a raw string, ex "fr.V.manger;fr.V.boufer"
        */
        reset_from_models: function(models){
            if ( _.isArray(models) === false  ){
                models = [models]
            }
            
            var data = [];
            _.each(models, function(model){
                attrs = model.pick('graph', 'lang', 'pos', 'form')
                var query_elem = new Models.TmuseQueryUnit(attrs);
                data.push(query_elem);
            });
            this.reset(data);
            
        },

        reset_from_str: function(query_str){
            var data = [];
            var qsplit = query_str.split(",");
            _.each(qsplit, function(qstr){
                var query_elem = new Models.TmuseQueryUnit();
                query_elem.set_from_str(qstr);
                data.push(query_elem);
            });
            this.reset(data);
        },

        reset_random: function(){
        /* reset collection with a random node
         * */
            var _this = this;
            $.ajax(
                    this.random_url,
                    {
                        success : function(data){
                            var unit = new Models.TmuseQueryUnit(data.doc);
                            _this.reset_from_models([unit]);
                        }
                    }
                );
        },

        to_string: function(){
            return this.models.map(function(qunit){ return qunit.to_string() }).join("; ");
        },

        validate: function(){
            return this.length > 0
        },

        export_for_engine: function(){
            return this.toJSON();
        },
    });


    // --- Clustering model ---
    // Clustering model and view

    function hide_cluster(cluster){

    };

    Models.Cluster = Cello.Cluster.extend({
        initialize : function(attrs, options){
            var _this = this;
            Models.Cluster.__super__.initialize.apply(this, arguments);
            
             this.on('add remove reset', function(){
                 _this.each(function(model){
                     model._compute_membership();
                     model._compute_colors();
                 })
             });
            
            this.on("change:color", function(){
                _this.members.vs.each( function(vertex){
                    vertex.set('color',_this.color);
                });
            });
            

            
            //add faded flag to the vs of the clusters not selected and remove faded flag to them if useful
            this.listenTo(this, "addflag:selected", function(){ 
                var other_clusters = _this.collection.without(_this);
                
                //if there is other selected clusters remove faded flag to its vertices
                _this.members.vs.each( function(vertex){
                      vertex.add_flag('cluster');
                });
                
                _(other_clusters).each(function(_this){
                    if (!_this.selected) {
                        _this.members.vs.each( function(vertex){
                            vertex.add_flag('cluster-faded');
                            _.each(vertex.incident(), function(edge){
                                    edge.add_flag('es-cluster-faded');
                            });
                        });
                    }
                });
            });
            //add faded flag to the vs of the clusters not selected
            this.listenTo(this, "rmflag:selected", this._unselect)

        },
        
        _unselect : function(){
                // remove flag cluster on the vertices of the current cluster
            this.members.vs.each( function(vertex){
                    vertex.remove_flag('cluster');
            });
            
            // remove faded flag on the vertices of all other clusters
            var other_clusters = this.collection.without(this);

            _(other_clusters).each(function(clust){
                clust.members.vs.each( function(vertex){
                    vertex.remove_flag('cluster-faded');
                _.each(vertex.incident(), function(edge){
                        edge.remove_flag('es-cluster-faded');
                    });
                });
            });

        }
    });


    // --- Graph model ---
    Models.Vertex = Cello.Vertex.extend({

        label: function(){
            return this.get('form');
        },
        
         _format_label : function(){
             // css should be in materials
            var font = ".normal-font"
                font = this.has_flag('form') ? '.form' : font 
                font = this.has_flag('target') ? '.target' : font 
            return [ {form : this.label(), css : font} ];
        },

        to_str : function(){
            var _this = this;
            return  _(['lang', 'pos', 'form'])
                        .map( function(e){ return _this.get(e)  })
                        .join('.');
        }
    },{ // !! static not in the same brackets !!
        active_flags : ['intersected', 'faded', 'selected']
    });

    // --- Graph model ---
    Models.Edge = Cello.Edge.extend({
    },{ // !! static not in the same brackets !!
        active_flags : ['intersected', 'faded', 'selected']
    });

    return Models;
});
