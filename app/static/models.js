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

    Models.Cluster = Cello.Cluster.extend({
        initialize : function(attrs, options){
            Models.Cluster.__super__.initialize.apply(this, arguments);
            _this = this;
            
            this.on("change:color", function(){
                this.members.vs.each( function(vertex){
                    vertex.set('cl_color',_this.color);
                });
            });
            
            
            //add faded flag to the vs of the clusters not selected and remove faded flag to them if useful
            this.listenTo(this, "addflag:selected", function(){ 
                var other_clusters = this.collection.without(this);
                
                //if there is other selected clusters remove faded flag to its vertices
                if(this.collection.selected.length > 1 ){
                    this.members.vs.each( function(vertex){
                          vertex.remove_flag('faded');
                    });
                }
                
                _(other_clusters).each(function(cluster){
                    if (!cluster.selected) {
                        cluster.members.vs.each( function(vertex){
                          vertex.add_flag('faded');
                        });
                    }
                });
            });
            //add faded flag to the vs of the clusters not selected
            this.listenTo(this, "rmflag:selected", function(){
                //if other clusters are still selected, just remove flag faded on the vertices of the current cluster
                if( this.collection.some_selected() ){
                    this.members.vs.each( function(vertex){
                        vertex.add_flag('faded');
                    });
                }
                // else remove faded flag on the vertices of all other clusters
                else { 
                    var other_clusters = this.collection.without(this);
                    _(other_clusters).each(function(cluster){
                        cluster.members.vs.each( function(vertex){
                            vertex.remove_flag('faded');
                        });
                    });
                }
            });
        }
    });


    // --- Graph model ---
    Models.Vertex = Cello.Vertex.extend({
         _format_label : function(){
             // css should be in materials
            return [ {form : this.get('form'), css : ".normal-font"} ];
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
