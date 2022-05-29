/*
Helper function to create 10m box centered on pixel centroid
--------------------------------------------------------------------------------


*/

function circle (location, radius) {
    const R = 6371; // Radius of the earth in km

    function distanceTo(point) {
        return distance(location, point)
    }

    function distance(a, b) {
        const lat1 = deg2rad(a.latitude)
        const lat2 = deg2rad(b.latitude)
        const deltaLatitude = deg2rad(a.latitude - b.latitude);
        const deltaLongitude = deg2rad(a.longitude - b.longitude);
        const x =
            haversine(deltaLatitude) +
            Math.cos(lat1) * Math.cos(lat2) * haversine(deltaLongitude)
        return Math.asin(Math.sqrt(x))*2*R;

    }

    function calculateOuterBounds() {
        const deltaLatitude = radius/R;
        const deltaLongitude = 2 * Math.asin(Math.sqrt(haversine(radius / R) / (Math.cos(deg2rad(location.latitude)) ** 2)))

        return {
            deltaLatitude: rad2deg(deltaLatitude),
            deltaLongitude: rad2deg(deltaLongitude)
        };
    }

    function haversine(theta) {
        return Math.sin(theta/2) ** 2
    }

    function deg2rad(deg) {
        return deg * (Math.PI/180)
    }

    function rad2deg(rad) {
        return rad * (180/Math.PI)
    }

    return {distanceTo, calculateOuterBounds}
}

// Script for MSI data display
// --------------------------------------------------------------------------------

// Declaring the map
var map = L.map('field-map-div');

L.tileLayer('https://a.tile.openstreetmap.de/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Agri smart'
}).addTo(map);

// L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',{
//     maxZoom: 20,
//     subdomains:['mt0','mt1','mt2','mt3']
// }).addTo(map);

map.options.minZoom = 13;
map.options.maxZoom = 18;
map.setZoom(14);

var field_footprint =  L.polygon(field_data.geometry,{color:"black",fillOpacity:0,}).addTo(map);
map.fitBounds(field_footprint._bounds);

if( field_data.is_empty == false)
{

   var array_lat  = field_data.latitude.split(',');
   var array_lon  = field_data.longitude.split(',');
   var array_ndvi = field_data.ndvi.split(',');

   var number_of_lines = array_lat.length -1;

   const radius = 0.005;

   const delta = 0.01;

   function getColor(n)
   {
      var hue = Math.floor((100 - n));
      //console.log("hsl(" + String(Math.floor(hue)) +"100%,50%)");
      return "hsl(" + String(Math.floor(100-hue)) +",100%,50%)";
   }


   for (var i = 0; i < number_of_lines; i++)
   {
      var lat  = parseFloat(array_lat[i]);
      var lon  = parseFloat(array_lon[i]);
      var ndvi = parseFloat(array_ndvi[i]);
      

      var colorclass = Math.floor((ndvi)/delta)-1;
      var theSpire = {latitude: lat, longitude: lon};
      var outerBounds = circle(theSpire, radius).calculateOuterBounds();
      var r = L.rectangle( [[lat - outerBounds.deltaLatitude,lon - outerBounds.deltaLongitude],[lat + outerBounds.deltaLatitude,lon + outerBounds.deltaLongitude]],{color:getColor(colorclass),fillOpacity:1,} );
      r.bindPopup("NDVI "+ndvi);
      r.on('mouseover', function (e) {
         this.openPopup();
      });
      r.on('mouseout', function (e) {
         this.closePopup();
      });

      r.addTo(map);
   }
}
