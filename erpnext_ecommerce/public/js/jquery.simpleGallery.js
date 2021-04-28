(function ($) {
    "use strict";

    var ver = 'simpleGallery-1.0.1';

    function debug(message) {
        if (window.console) {
            console.log(message);
        }
    }

    $.fn.simpleGallery = function (options) {
        var opts = $.extend({}, $.fn.simpleGallery.defaults, options);

        if (this.length <= 0) {
            debug('There are no thumbnails in the gallery');
            return false;
        }

        this.each(function () {
            var img = $('<img>');
            img.src = $(this).attr('rel');
        });

        var init = function () {
            var parent_anchor =  $(this).parents(opts.thumbnail_anchor),
                src = parent_anchor.attr(opts.big_image_attr),
                type = parent_anchor.attr(opts.type),
                lens_image = parent_anchor.attr(opts.lens_image_attr),
                youtube_id = parent_anchor.attr(opts.youtube_id_attr);
            var image_container = $(this).parents(opts.gallery_container).find(opts.big_image_container);
            var loading_image = $('<img>', {'src': opts.loading_image});
            image_container.html(loading_image);
            if(type =="Image"){
                var attr = $('<a onclick="light_gallery(this)">').attr('data-lens-image',lens_image);
                // For some browsers, `attr` is undefined; for others,
                // `attr` is false.  Check for both.
                if (typeof attr !== typeof undefined && attr !== false) {
                    var a = $('<a onclick="light_gallery(this)">').attr('data-lens-image', lens_image).addClass(opts.parent_anchor_class);
                    var img = $('<img>').load(function(){
                        img.appendTo(a);
                        image_container.html(a);
                    }).attr('src', src).addClass(opts.big_image_class);
                }
            }

            if(type =="Video"){
                var video_id =$('<a onclick="light_gallery(this)">').attr('data-youtube-id',youtube_id);
                var video_type = parent_anchor.attr(opts.videotype)
                // For some browsers, `attr` is undefined; for others,
                // `attr` is false.  Check for both.
                if(typeof video_id !== typeof undefined && video_id !== false){
                    if(video_type == "youtube"){
                        var html=''
                        html +='<iframe style="width:100%;height:100%;" src="https://www.youtube.com/embed/'+youtube_id+'"></iframe>';
                        image_container.html(html);
                    }else if(video_type == "vimeo"){
                        var html=''
                        html +='<iframe style="width:100%;height:100%;" src="https://player.vimeo.com/video/'+youtube_id+'"></iframe>';
                        image_container.html(html);
                    }else if(video_type == "other"){
                        var html=''
                        html +='<video class="lg-video-object lg-html5 video-js vjs-default-skin" style="width:100%;height:100%;" controls><source src="'+youtube_id+'"></video>';
                        image_container.html(html);
                    }
                }
            }
            

        };

        $(this).on(opts.show_event, init);

        return this;
    };

    $.fn.simpleGallery.ver = function () { return ver; };

    $.fn.simpleGallery.defaults = {
        thumbnail_anchor: '.simpleLens-thumbnail-wrapper',
        big_image_class: 'simpleLens-big-image',
        type: 'data-type',
        videotype: 'data-videotype',
        lens_image_attr: 'data-lens-image',
        youtube_id_attr: 'data-youtube-id',
        big_image_attr: 'data-big-image',
        parent_anchor_class: 'simpleLens-lens-image',
        gallery_container: '.simpleLens-gallery-container',
        big_image_container: '.simpleLens-big-image-container',
        loading_image: 'images/loading.gif',
        show_event: 'mouseenter'
    };

})( jQuery );