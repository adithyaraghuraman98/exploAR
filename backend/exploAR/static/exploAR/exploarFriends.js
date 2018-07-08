var vrDisplay, vrControls, arView;
var canvas, camera, scene, renderer;
var raycaster, mouse, clicked;
var foundNegZ, angleNegZ, initLat, initLong;

var scouts = new Map();

/**
 * Use the `getARDisplay()` utility to leverage the WebVR API
 * to see if there are any AR-capable WebVR VRDisplays. Returns
 * a valid display if found. Otherwise, display the unsupported
 * browser message.
 */

THREE.ARUtils.getARDisplay().then(function (display) {
  if (display) {
    vrDisplay = display;
    init();
  } else {
    THREE.ARUtils.displayUnsupportedMessage();
  }
});

function init() {
  // Calls getLocation() every 5 seconds to update POIs
  //window.onload = getLocation;
  window.setInterval(updateSprites, 5000);

  // Setup the three.js rendering environment

  renderer = new THREE.WebGLRenderer({ alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.autoClear = false;
  canvas = renderer.domElement;
  document.body.appendChild(canvas);
  scene = new THREE.Scene();

  // Creating the ARView, which is the object that handles
  // the rendering of the camera stream behind the three.js
  // scene
  arView = new THREE.ARView(vrDisplay, renderer);

  // The ARPerspectiveCamera is very similar to THREE.PerspectiveCamera,
  // except when using an AR-capable browser, the camera uses
  // the projection matrix provided from the device, so that the
  // perspective camera's depth planes and field of view matches
  // the physical camera on the device.
  camera = new THREE.ARPerspectiveCamera(
    vrDisplay,
    60,
    window.innerWidth / window.innerHeight,
    vrDisplay.depthNear,
    vrDisplay.depthFar
  );

  // VRControls is a utility from three.js that applies the device's
  // orientation/position to the perspective camera, keeping our
  // real world and virtual world in sync.
  vrControls = new THREE.VRControls(camera);

  // Initialize raycaster and mouse to determine clicked objects.
  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();

  // Bind our event handlers
  window.addEventListener('resize', onWindowResize, false);
  window.addEventListener( 'touchstart', onTouch, false );
  if (window.DeviceOrientationEvent) {
    window.addEventListener('deviceorientation', onOrientation, true);
  }
  // Kick off the render loop!
  update();

}

/**
 * The render loop, called once per frame. Handles updating
 * our scene and rendering.
 */
function update() {
  // Clears color from the frame before rendering the camera (arView) or scene.
  renderer.clearColor();

  // Render the device's camera stream on screen first of all.
  // It allows to get the right pose synchronized with the right frame.
  arView.render();

  // Update our camera projection matrix in the event that
  // the near or far planes have updated
  camera.updateProjectionMatrix();

  // Update our perspective camera's positioning
  vrControls.update();

  if (clicked) {
    // update the picking ray with the camera and mouse position
    raycaster.setFromCamera( mouse, camera );

    // calculate objects intersecting the picking ray
    var intersects = raycaster.intersectObjects( scene.children );

    if (intersects.length > 0) {
      var obj = intersects[0].object;
      if (obj instanceof THREE.Sprite & obj.name != "distance") {
        window.location.href = ('https://exploar.us/profilePage/'+scouts.get(obj).user);
      }
    }
    clicked = false;
  }

  // Render our three.js virtual scene
  renderer.clearDepth();
  renderer.render(scene, camera);


  // Kick off the requestAnimationFrame to call this function
  // when a new VRDisplay frame is rendered
  vrDisplay.requestAnimationFrame(update);
}

function getLocation() {
  if (foundNegZ.get() == true) {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(showPosition);
    } else { 
        alert("Geolocation is not supported by this browser.");
    }
  }
}

function updateSprites() {
  if (foundNegZ.get() == true) {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(resizeSprites);
    } else { 
        alert("Geolocation is not supported by this browser.");
    }
  }
}

function resizeSprites(position) {
  if (position) {
    latDeg = position.coords.latitude;
    longDeg = position.coords.longitude;

    latitude = (Math.PI/180)*latDeg;
    longitude = (Math.PI/180)*longDeg;

    for (var [sprite, info] of scouts) {
      var metricDistance = distanceLatLng(latitude, info.lat, longitude, info.lng); // in meters
      var milesDistance = metricDistance * 0.000621371;

      var metricToJs = (5/8);
      var jsDistance = metricDistance*metricToJs;

      var fontsize = 18;
      var fontsizedist = 15;

      var minScale = 1;
      var maxScale = 4;
      var scale = (jsDistance/100)*(maxScale-minScale);

      if (scale < 0.75) {
        scale = 0.75;
      }

      sprite.position.set(sprite.position.x, jsDistance*.01 + scale, sprite.position.z);
      sprite.scale.set(0.5 * scale * fontsize, 0.25 * scale * fontsize, 0.75 * scale * fontsize);

      var opacity = 1.0 - milesDistance;

      if (opacity < 0.75) {
        opacity = 0.75;
      }

      var dist = makeTextSprite(" "+milesDistance.toString().substring(0, 4)+" miles", 
        {"fontsize": 15, "textColor": { r:255, g:255, b:255, a:1.0 }, "backgroundColor": { r:0, g:0, b:0, a:opacity }});
      dist.name = "distance";

      dist.scale.set(0.5 * scale * fontsizedist, 0.25 * scale * fontsizedist, 0.75 * scale * fontsizedist);
      dist.position.set(info.dist.position.x, jsDistance*.01 + scale*2, info.dist.position.z);
      
      scene.add(dist);
      scene.remove(info.dist);

      info.dist = dist;
    }
  }
}

function recalibrate() {
  location.reload();
}

function showPosition(position) {

  if (position) {

      latDeg = position.coords.latitude;
      longDeg = position.coords.longitude;

      latitude = (Math.PI/180)*latDeg;
      longitude = (Math.PI/180)*longDeg;

      if (document.getElementById("place-id").value == "") {
        // remove all elements from scene
          while(scene.children.length > 0){ 
              scene.remove(scene.children[0]); 
          }
          scouts.clear();

        $.ajax({
            url: "/get-scouts-json",
            type: "GET",
            dataType : "json",
            success: function(response) {
              if (response[0]["fields"]) {
                for(var i = 0; i < response.length; i++) {
                  res = response[i];
                  fields = res["fields"];

                  placeScout(fields, latitude, longitude);
                }
                resizeSprites(position);
              }
            }
        });
      } else {
            $.ajax({
              url: "/get-destination-json",
              type: "GET",
              data: "place_id="+document.getElementById("place-id").value,
              dataType : "json",
              success: function(response) {
                // remove all elements from scene
                while(scene.children.length > 0){ 
                    scene.remove(scene.children[0]); 
                }
                places.clear();

                res = response[0];
                fields = res["fields"];

                placeObject(fields, latitude, longitude);
                
                resizeSprites(position);
              }
            });
      }
  }
}

function placeScout(fields, latitude, longitude) {
  var lat = (Math.PI/180)*fields["latitude"];
  var lng = (Math.PI/180)*fields["longitude"];
  
  var brng = bearingLatLng(latitude, lat, longitude, lng); 
  var metricDistance = distanceLatLng(latitude, lat, longitude, lng); // in meters
  var milesDistance = metricDistance * 0.000621371;

  var metricToJs = (5/8);
  var jsDistance = metricDistance*metricToJs;
  
  var newBrng = brng-angleNegZ;
  var xCube = jsDistance*Math.sin(newBrng);
  var yCube = jsDistance*.01;
  var zCube = -jsDistance*Math.cos(newBrng);

  var geometry = new THREE.OctahedronGeometry(1, 1, 1);
  var material = new THREE.MeshBasicMaterial( {color: 0xffff00, wireframe: true} );
  var cone = new THREE.Mesh( geometry, material );
  cone.name = 'cone';
  cone.position.set(xCube, yCube, zCube);
  scene.add( cone );

  var opacity = 1.0 - milesDistance;

  if (opacity < 0.75) {
    opacity = 0.75;
  }

  // add sprite label to scene
  sprite = makeTextSprite(" "+fields["user"], {"backgroundColor": { r:255, g:255, b:0, a:opacity }});
  sprite.name = fields["user"];
  sprite.position.set(xCube, yCube, zCube);
  scouts.set(sprite, { user: fields["user"], lat: lat, lng: lng});
  scene.add(sprite);

  dist = makeTextSprite(" "+milesDistance.toString().substring(0, 4)+" miles", 
    {"fontsize": 15, "textColor": { r:255, g:255, b:255, a:1.0 }, "backgroundColor": { r:0, g:0, b:0, a:opacity }});
  dist.name = "distance";
  dist.position.set(xCube, yCube, zCube);
  scouts.get(sprite).dist = dist;
  scene.add(dist);
}

function makeTextSprite(message, parameters) {
    if (parameters === undefined) parameters = {};

    var fontsize = parameters.hasOwnProperty("fontsize") ? parameters["fontsize"] : 18;
    var fontface = parameters.hasOwnProperty("fontface") ? parameters["fontface"] : "Helvetica";
    var borderThickness = 2;
    var borderColor = { r:0, g:0, b:0, a:1.0 };
    var backgroundColor = parameters.hasOwnProperty("backgroundColor") ? parameters["backgroundColor"] : { r:255, g:255, b:255, a:1.0 };
    var textColor = parameters.hasOwnProperty("textColor") ? parameters["textColor"] : { r:0, g:0, b:0, a:1.0 };

    var canvas = document.createElement('canvas');
    var context = canvas.getContext('2d');
    context.font = "Bold " + fontsize + "px " + fontface;
    var metrics = context.measureText( message );
    var textWidth = metrics.width;

    context.fillStyle   = "rgba(" + backgroundColor.r + "," + backgroundColor.g + "," + backgroundColor.b + "," + backgroundColor.a + ")";
    context.strokeStyle = "rgba(" + borderColor.r + "," + borderColor.g + "," + borderColor.b + "," + borderColor.a + ")";

    context.lineWidth = borderThickness;
    roundRect(context, borderThickness/2, borderThickness/2, (textWidth + borderThickness) * 1.1, fontsize * 1.4 + borderThickness, 2);

    context.fillStyle = "rgba("+textColor.r+", "+textColor.g+", "+textColor.b+", 1.0)";
    context.fillText( message, borderThickness, fontsize + borderThickness);

    var texture = new THREE.Texture(canvas) 
    texture.needsUpdate = true;

    var spriteMaterial = new THREE.SpriteMaterial( { map: texture, useScreenCoordinates: false } );
    var sprite = new THREE.Sprite( spriteMaterial );
    sprite.scale.set(0.5 * fontsize, 0.25 * fontsize, 0.75 * fontsize);
    return sprite;  
}

function roundRect(ctx, x, y, w, h, r) { 
  ctx.beginPath(); 
  ctx.moveTo(x + r, y); 
  ctx.lineTo(x + w - r, y); 
  ctx.quadraticCurveTo(x + w, y, x + w, y + r); 
  ctx.lineTo(x + w, y + h - r); 
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); 
  ctx.lineTo(x + r, y + h); 
  ctx.quadraticCurveTo(x, y + h, x, y + h - r); 
  ctx.lineTo(x, y + r); 
  ctx.quadraticCurveTo(x, y, x + r, y); 
  ctx.closePath(); 
  ctx.fill(); 
  ctx.stroke(); 
} 

function distanceLatLng(lat1, lat2, lon1, lon2) {
  
    //Haversine formula 
    var dlon = lon2 - lon1;
    var dlat = lat2 - lat1;
    var a = Math.sin(dlat / 2)**2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2)**2;

    var c = 2 * Math.asin(Math.sqrt(a));
   
    //Radius of earth in kilometers. Use 3956 for miles
    var r = 6371;
    
    //calculate the result in meters
    return 1000*(c * r);
}

function bearingLatLng(lat1, lat2, lon1, lon2) {
  var y = Math.sin(lon2-lon1) * Math.cos(lat2);
  var x = Math.cos(lat1)*Math.sin(lat2) -
          Math.sin(lat1)*Math.cos(lat2)*Math.cos(lon2-lon1);
  return Math.atan2(y, x);
}

/**
 * On window resize, update the perspective camera's aspect ratio,
 * and call `updateProjectionMatrix` so that we can get the latest
 * projection matrix provided from the device
 */
function onWindowResize () {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function onTouch( event ) {
  // calculate mouse position in normalized device coordinates
  // (-1 to +1) for both components
  clicked = true;

  mouse.x = ( event.pageX / window.innerWidth ) * 2 - 1;
  mouse.y = - ( event.pageY / window.innerHeight ) * 2 + 1;
}

function onOrientation(event) {
  if((event.webkitCompassHeading) && (foundNegZ.get() == false)) {
    // Apple works only with this, alpha doesn't work
    compassdir = event.webkitCompassHeading;
    angleNegZ = compassdir*(Math.PI/180);
    foundNegZ.set(true);
  }
}

function Wrapper(callback) {
    var value;
    this.set = function(v) {
      value = v;
      callback(this);
    }
    this.get = function() {
      return value;
    }  
}

foundNegZ = new Wrapper(getLocation);
foundNegZ.set(false);
