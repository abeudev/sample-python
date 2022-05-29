// Declaring the map
var map = L.map('create-field-map-div');
// map.setView([45.1544, 10.7896], 13);
map.setView([5.349390, -4.017050], 13);

// Tileset
L.tileLayer('https://a.tile.openstreetmap.de/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Agri Smart'
}).addTo(map);

map.options.minZoom = 14;
map.options.maxZoom = 18;

var popup = L.popup();
var create_field_is_clicked = false;
var points = new Array();
var polyline = L.polyline(points).addTo(map);
var polygon_field;
var marker;

function onMapClick(e)
{
    if(create_field_is_clicked)
    {
      polyline.remove();
      latLng = e.latlng
      points.push([latLng.lat,latLng.lng]);
      L.marker(latLng).addTo(map);
      polyline = L.polyline(points).addTo(map);
   }
}

map.on('click', onMapClick);

function create_field_clicked()
{
   var element = document.getElementById("create_field_btn");

   if( element.textContent == "Définir parcelle")
   {
      element.classList.remove("btn-success");
      element.classList.add("btn-danger");
      element.textContent="Enregistrer parcelle";
      create_field_is_clicked = true;
   }
   else
   {
         element.classList.remove("btn-danger");
         element.classList.add("btn-success");
         element.textContent="Définir parcelle";
         create_field_is_clicked = false;

         geometry_string = ''

         for (var i = 0; i < points.length; i++)
         {
            geometry_string += points[i][0] + ','+ points[i][1] + ','
         }

         geometry_string = geometry_string.substring(0, geometry_string.length - 1);
         document.getElementById("field-geometry").value = geometry_string;
         document.getElementById("field-geometry").data = true;
         polygon_field = L.polygon(points).addTo(map);
         

         points = new Array();
   }

}
