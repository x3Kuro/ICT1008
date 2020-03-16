var map = null;
var i;


$(function() {
  $('button#submit').bind('click', function() {
    map.spin(true);
    $.getJSON('/data', {
      source: $('input[name="source"]').val(),
      dest: $('input[name="dest"]').val(),
    }, function(data) {
        map.spin(false);
        plotMap(data.path, data.start, data.start_road);
      });
    return false;
  });
});

function plotMap(path, src, start_rd) {

    if (map != undefined && map != null) {
        map.remove();
    }

    map = L.map('map', {
        fullscreenControl: true,
        fullscreenControlOptions: {
            position: 'topleft'
      }
    }).setView([1.4052, 103.9024], 18);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    if (src != undefined && src != null){
        var src_marker = L.marker(src).addTo(map)
            .bindPopup(start_rd)
    }

    if (path != undefined){
        var paths = L.featureGroup();
        paths.addTo(map);
        var walk_line = L.polyline(path[0], {
            opacity: 0,
            smoothFactor: 1
        }).addTo(map);

        var decorator = L.polylineDecorator(walk_line, {
            patterns: [
                // dash lines every 18px, for 1px size
                {offset: 0, repeat: 18, symbol: L.Symbol.dash({pixelSize: 1, pathOptions: {color: '#0072d9', weight:10}})}
            ]
        }).addTo(paths);

        if (path.length == 2){
            var train_line = L.polyline(path[2], {
                color:'red',
                width: 8,
                opacity: 1,
                smoothFactor: 1
            }).addTo(paths);
        }
        else if (path.length == 3){
            var train_line = L.polyline(path[2], {
                color:'red',
                width: 8,
                opacity: 1,
                smoothFactor: 1
            }).addTo(paths);

            var walk2_line = L.polyline(path[1], {
                opacity: 0,
                smoothFactor: 1
            }).addTo(paths);

            var walk2_decorator = L.polylineDecorator(walk2_line, {
                patterns: [
                    // dash lines every 18px, for 1px size
                    {offset: 0, repeat: 18, symbol: L.Symbol.dash({pixelSize: 1, pathOptions: {color: '#0072d9', weight:10}})}
                ]
            }).addTo(paths);
        }

        // Ensure map shows the full route in start zoom
        map.fitBounds(paths.getBounds());

    }
}
