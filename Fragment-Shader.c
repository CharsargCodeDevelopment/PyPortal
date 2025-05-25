#version 330 core



#ifdef GL_ES
precision mediump float;
#endif
out vec4 fragColor;
out vec4 normalColor;

// Function to create a pseudo-random gradient vector
vec2 randomGradient(vec2 coord) {
    float random = fract(sin(dot(coord, vec2(127.1, 311.7))) * 43758.5453);
    float angle = random * 2.0 * 3.14159265359; // Random angle in radians
    return vec2(cos(angle), sin(angle));
}

// Fade function for smoothing
float fade(float t) {
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

// Linear interpolation
float lerp(float a, float b, float t) {
    return a + t * (b - a);
}

// Perlin noise function
float perlinNoise(vec2 uv) {
    // Grid cell coordinates
    vec2 p0 = floor(uv);
    vec2 p1 = p0 + vec2(1.0, 0.0);
    vec2 p2 = p0 + vec2(0.0, 1.0);
    vec2 p3 = p0 + vec2(1.0, 1.0);

    // Local coordinates within the cell
    vec2 local = fract(uv);

    // Fade curves for interpolation
    vec2 fadeVals = vec2(fade(local.x), fade(local.y));

    // Compute dot products between gradient vectors and local position vectors
    float d0 = dot(randomGradient(p0), local - vec2(0.0, 0.0));
    float d1 = dot(randomGradient(p1), local - vec2(1.0, 0.0));
    float d2 = dot(randomGradient(p2), local - vec2(0.0, 1.0));
    float d3 = dot(randomGradient(p3), local - vec2(1.0, 1.0));

    // Interpolate the results along x and y axes
    float xInterp1 = lerp(d0, d1, fadeVals.x);
    float xInterp2 = lerp(d2, d3, fadeVals.x);
    return lerp(xInterp1, xInterp2, fadeVals.y);
}


uniform vec2 resolution;
uniform vec3 camera_pos;
uniform vec3 camera_dir;
uniform vec3 light_positions[64];
uniform vec3 light_colors[64];
uniform int light_count;

uniform vec4 metaballs[64];
uniform int metaballcount;

uniform vec4 ObjectsMeshes[64];
uniform float ObjectID[64];
uniform float ObjectIDList[64];

uniform int ObjectCount;
uniform int ObjectMeshCount;

uniform vec4 Portals[16];
uniform int PortalCount = 0;
uniform int OtherPortalIndex[16];

uniform float time;

uniform sampler3D texture3D;

uniform float isObjectMatte[64];

bool isObjectAt(vec3 point) {
    //if (point.y < -2){
    //    return true;

    //}
    float TotalDistance = 0;
    for (int i = 0; i < metaballcount; i++) {
        vec3 center = metaballs[i].xyz;
        float radius = metaballs[i].w;
        if (distance(point,center) > 0){
            TotalDistance += radius/(distance(point,center));
        }
        if (distance(point, center) <= radius) {
            //return true;
        }
    if (TotalDistance > metaballcount){
    return true;
    }
    }
    return false;
    
}


bool CollidingWithPortal(vec3 point){
    for (int i = 0; i < PortalCount;i++){
        vec4 portal = Portals[i];
        vec3 center = portal.xyz;
        float radius = portal.w;
        if ((center-point).z > 0){
            return false;
        }

        //if ((center-point).z < -0.1){
        //    return false;
       // }
        //return true;
        if (distance(point, center) <= radius){
        if (distance(point, center) <= radius-0.2){
            return false;
        }
        //vec4 OtherPortal = Portals[OtherPortalIndex[i]];
        //vec3 PortalOffset = portal.xyz - OtherPortal.xyz;
            return true;
        }
    }
    return false;
}

bool CollidingWithPortalFrame(vec3 point){
    for (int i = 0; i < PortalCount;i++){
        vec4 portal = Portals[i];
        vec3 center = portal.xyz;
        float radius = portal.w;
        if ((center-point).z > 0.1){
            return false;
        }
        if ((center-point).z < -0.1){
            return false;
        }
        if (distance(point, center) <= radius+0.2){
        if (distance(point, center) <= radius-0.2){
            return false;
        }
        //vec4 OtherPortal = Portals[OtherPortalIndex[i]];
        //vec3 PortalOffset = portal.xyz - OtherPortal.xyz;
            return true;
        }
    }
    return false;
}



vec3 GetPortalRayOffset(vec3 point){
    for (int i = 0; i < PortalCount;i++){
        vec4 portal = Portals[i];
        vec3 center = portal.xyz;
        float radius = portal.w;
        if ((center-point).z > 0){
            return vec3(0.0,0.0,0.0);
        }
        if (distance(point, center) <= radius){
        if (distance(point, center) <= radius-0.2){
            return vec3(0.0,0.0,0.0);
        }
        vec4 OtherPortal = Portals[OtherPortalIndex[i]];
        //vec3 PortalOffset = portal.xyz - OtherPortal.xyz;
        vec3 PortalOffset = OtherPortal.xyz - portal.xyz;
        
            
            return PortalOffset;


        }

    }
    return vec3(0.0,0.0,0.0);



}

vec3 calculateNormal(vec3 point) {
    float eps = 0.01; // Small offset for finite difference calculation
    float value = 0.0;

    int closestIndex = 0;
    float closestDistance = distance(point,metaballs[closestIndex].xyz);

    // Evaluate the scalar field at the given point
    for (int i = 0; i < metaballcount; i++) {
        vec3 center = metaballs[i].xyz;
        float radius = metaballs[i].w;
        float dist = distance(point, center);
        if (dist < closestDistance){
            closestIndex = i;
            closestDistance = distance(point,metaballs[closestIndex].xyz);


        }
        if (dist > 0.0) {
            value += radius / dist;
        }
    }

    // Approximate the partial derivatives using finite differences
    float dx = 0.0, dy = 0.0, dz = 0.0;

    for (int i = 0; i < metaballcount; i++) {
        vec3 center = metaballs[i].xyz;
        float radius = metaballs[i].w;

        dx += (radius / distance(point + vec3(eps, 0.0, 0.0), center)) - (radius / distance(point - vec3(eps, 0.0, 0.0), center));
        dy += (radius / distance(point + vec3(0.0, eps, 0.0), center)) - (radius / distance(point - vec3(0.0, eps, 0.0), center));
        dz += (radius / distance(point + vec3(0.0, 0.0, eps), center)) - (radius / distance(point - vec3(0.0, 0.0, eps), center));
    }
    vec3 center = metaballs[closestIndex].xyz;
    float radius = metaballs[closestIndex].w;
    dx = (radius / distance(point + vec3(eps, 0.0, 0.0), center)) - (radius / distance(point - vec3(eps, 0.0, 0.0), center));
    dy = (radius / distance(point + vec3(0.0, eps, 0.0), center)) - (radius / distance(point - vec3(0.0, eps, 0.0), center));
    dz = (radius / distance(point + vec3(0.0, 0.0, eps), center)) - (radius / distance(point - vec3(0.0, 0.0, eps), center));

    // Combine the partial derivatives into the gradient
    vec3 gradient = vec3(dx, dy, dz) / (2.0 * eps);
    //vec3 gradient = vec3(dx, dy, dz);
    return normalize(gradient); // Normalize to get the unit normal
}

vec3 calculateObjectNormal(vec3 point,float ID) {
    float eps = 0.01; // Small offset for finite difference calculation
    float value = 0.0;

    int closestIndex = 0;
    
    float closestDistance = distance(point,ObjectsMeshes[closestIndex].xyz);

    closestDistance = 1000;

    // Evaluate the scalar field at the given point
    for (int i = 0; i < ObjectMeshCount; i++) {
        if (ObjectID[i]== ID){
        vec3 center = ObjectsMeshes[i].xyz;
        float radius = ObjectsMeshes[i].w;
        float dist = distance(point, center);
        if (dist < closestDistance){
            closestIndex = i;
            closestDistance = distance(point,metaballs[closestIndex].xyz);
            }
        if (dist > 0.0) {
            value += radius / dist;
        }
        
    }
    }

    // Approximate the partial derivatives using finite differences
    float dx = 0.0, dy = 0.0, dz = 0.0;

    for (int i = 0; i < metaballcount; i++) {
        if (ObjectID[i] == ID){
        vec3 center = ObjectsMeshes[i].xyz;
        float radius = ObjectsMeshes[i].w;

        dx += (radius / distance(point + vec3(eps, 0.0, 0.0), center)) - (radius / distance(point - vec3(eps, 0.0, 0.0), center));
        dy += (radius / distance(point + vec3(0.0, eps, 0.0), center)) - (radius / distance(point - vec3(0.0, eps, 0.0), center));
        dz += (radius / distance(point + vec3(0.0, 0.0, eps), center)) - (radius / distance(point - vec3(0.0, 0.0, eps), center));
        }
    }
    vec3 center = ObjectsMeshes[closestIndex].xyz;
    float radius = ObjectsMeshes[closestIndex].w;
    dx = (radius / distance(point + vec3(eps, 0.0, 0.0), center)) - (radius / distance(point - vec3(eps, 0.0, 0.0), center));
    dy = (radius / distance(point + vec3(0.0, eps, 0.0), center)) - (radius / distance(point - vec3(0.0, eps, 0.0), center));
    dz = (radius / distance(point + vec3(0.0, 0.0, eps), center)) - (radius / distance(point - vec3(0.0, 0.0, eps), center));

    // Combine the partial derivatives into the gradient
    vec3 gradient = vec3(dx, dy, dz) / (2.0 * eps);
    //vec3 gradient = vec3(dx, dy, dz);
    return normalize(gradient); // Normalize to get the unit normal
}





vec3 RotateOnX(vec3 Point,float angle){
    float rotatedY = (sin(angle) * Point.y)-(cos(angle) * Point.z);
    float rotatedZ = (cos(angle) * Point.y)+(sin(angle) * Point.z);
    return vec3(Point.x,rotatedY,rotatedZ);
}
vec3 RotateOnY(vec3 Point,float angle){
    float rotatedX = (sin(angle) * Point.x)-(cos(angle) * Point.z);
    float rotatedZ = (cos(angle) * Point.x)+(sin(angle) * Point.z);
    return vec3(rotatedX,Point.y,rotatedZ);
}

float insideBox3D(vec3 v, vec3 bottomLeft, vec3 topRight) {
    vec3 s = step(bottomLeft, v) - step(topRight, v);
    return s.x * s.y * s.z; 
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution * 2.0 - 1.0;
    uv.y *= resolution.y / resolution.x;

    //uv.x += perlinNoise(uv);

    vec3 ray_origin = camera_pos;
    
    vec3 ray_dir = normalize(vec3(uv.x, uv.y, -1.0)); // Ray direction in view space
    //ray_dir.x += distance(randomGradient(uv+(1/time)),vec2(0,0));
    ray_dir = normalize(ray_dir);
    //ray_dir = vec3()r;
    float Cam_XAngle = camera_dir.x;
    float Cam_YAngle = camera_dir.y;
    ray_dir = RotateOnX(ray_dir,Cam_XAngle);
    ray_dir = RotateOnY(ray_dir,Cam_YAngle);
   // ray_dir = vec3((sin(Cam_XAngle)*uv.x)-(cos(Cam_XAngle)*uv.z),uv.y,(cos(Cam_XAngle)*uv.x)+(sin(Cam_XAngle)*uv.z));
    ray_dir = normalize(ray_dir);

    bool insidePortal = false;

    float max_distance = 50.0;
    max_distance = 10.0;
    float step_size = 0.01;
    float traveled_distance = 0.0;
    vec3 current_pos = ray_origin;
    bool hit = false;
    //hit = true;
    float b = 0;
    vec3 light_color = vec3(0,0,0);
    vec3 normal = vec3(0,1,0);
    vec3 color_filter = vec3(1,1,1);
    float portal_distortion_multiplier = 1;
    for (float t = 0.0; t < max_distance; t += step_size) {
        step_size = 0.01 + (t*0.01);
        current_pos += ray_dir * step_size;
        b += 1/(max_distance+step_size);
        for (int i = 0; i < light_count; i++) {
            vec3 light_position = light_positions[i];
            if (distance(light_position,current_pos) < 1){
                hit = true;
                b = b*0.1;
                ray_dir = vec3(0,0,0);
                light_color = vec3(light_colors[i]);
                break;
            }
        }
        if (current_pos.y < -2){
            if (current_pos.y > -2.2){ 
            hit=true;
            normal = vec3(0,1,0);
            vec3 I = (ray_dir/normalize(ray_dir));
            vec3 N = (normal/normalize(normal));
            ray_dir = vec3(ray_dir.x,-(ray_dir.y),ray_dir.z);

            //if (current_pos.y > -2.2){ 
            bool onLines = false;
            if (mod(current_pos.x,1) > 0.9){
                onLines = true;

            }
            if (mod(current_pos.z,1) > 0.9){
                onLines = true;
                

            }
            if (onLines == true){
                light_color = vec3(1.0,1.0,1.0);
            b=0;
            break;
            }
            }
            //ray_dir = I - 2 * dot(I,N) * N;
            //b = 0;
            //b = 0;
            //break;


        }


        if (CollidingWithPortalFrame(current_pos)){
            hit = true;
            light_color = vec3(255,154,0)/255;
            b = 0;
            break;


        }
        if (CollidingWithPortal(current_pos)){
            //break;
            //hit = true;
            //b = 1;
            //b = 0;
            
            if (insidePortal == false){
            //ray_dir.x += distance(randomGradient(uv+(1/time)),vec2(0,0))*portal_distortion_multiplier;
            //portal_distortion_multiplier = -portal_distortion_multiplier;
            //color_filter = color_filter*(vec3(255,154,0)/255);
            current_pos = current_pos + GetPortalRayOffset(current_pos);
            //ray_dir = ray_dir * vec3(1,1,-1);
            //ray_dir.z = -abs(ray_dir.z);
            }
            //current_pos = current_pos + GetPortalRayOffset(current_pos);
            insidePortal = true;
            //light_color = vec3(0,0,1);
            //break;


        }
        else {
        insidePortal = false;

        }
        if (isObjectAt(current_pos)) {
            //b = 0;
            hit = true;

            float matte1 = 1.0;
            if (matte1 == 0){
                //t++;
                //current_pos += ray_dir;
                normal = calculateNormal(current_pos);
                //normal = vec3(0,1,0);
                vec3 I = (ray_dir/normalize(ray_dir));
                vec3 N = (normal/normalize(normal));
                ray_dir = I - 2 * dot(I,N) * N;
                //ray_dir = vec3(0,1,0);
                //ray_dir.y += perlinNoise(uv);
                ray_dir = -normal;
                //ray_dir.y = -(ray_dir.y);
                //break;w
            }
            else {
                for (int i = 0; i < light_count; i++) {
                vec3 light_position = light_positions[i];
                vec3 light_normal = normalize(light_position-current_pos);
                b = 0;
                light_color += vec3(light_colors[i])*dot(light_normal,normal);
        }
        break;

            }
        }
        bool Collision = false;
        for (int i=0;i<ObjectCount;i++){
            
            float CurrentObjectID = ObjectIDList[i];
            int CurrentObjectMetaballCount = 0;
            float TotalDistance = 0;
            
            for (int j = 0;j < ObjectMeshCount;j++){
                
                if (ObjectID[j] == CurrentObjectID){


                    
                    //for (int i = 0; i < metaballcount; i++) {
                    vec3 center = ObjectsMeshes[j].xyz;
                    float radius = ObjectsMeshes[j].w;
                    if (distance(current_pos,center) > 0){
                    TotalDistance += radius/(distance(current_pos,center));
                    }
                    if (distance(current_pos, center) <= radius) {
                        //return true;
                     }

                }
             if (TotalDistance > 2){
                    float matte = isObjectMatte[j];
                    //return true;
                    hit = true;
                    
                    normal = calculateObjectNormal(current_pos,CurrentObjectID);
                    vec3 I = (ray_dir/normalize(ray_dir));
                    vec3 N = (normal/normalize(normal));
                    if (matte<0.5){
                    
                    
                    
                    //ray_dir = I - 2 * dot(I,N) * N;
                    ray_dir = -normal;
                    //light_color = vec3(1,0,0);
                    //light_color = abs(normal);
                    //b = 0;
                    //b = 0;
                    }else {
                        Collision = true;
                        for (int k = 0; k < light_count; k++) {
                            vec3 light_position = light_positions[k];
                            vec3 light_normal = normalize(light_position-current_pos);
                            b = 0;
                            light_color += vec3(light_colors[k])*-dot(light_normal,normal);
                            //light_color = normal;
                        }
                    break;

                    }
                    
                    break;

                    }
                     //}
            }
        if (Collision == true){
            break;

        }

        }
        if (Collision == true){
            break;

        }
        if (insideBox3D(current_pos,vec3(0,0,0),vec3(1,1,1))>0){
            //
            //light_color = current_pos;
            //color_filter *= normalize(texture(texture3D,current_pos.xyz).rgb+vec3(1,1,1));
            if (texture(texture3D,current_pos.xyz).xyz == vec3(0,0,0)){
                
                //color_filter = vec3(1,1,1);
            }else{
                hit = true;
                light_color = texture(texture3D,current_pos.xyz).xyz;
                b = 0;
                break;
                
            }
            
            //b=0;
            //break;


        }
    }

    if (hit) {
        b = 1-b;
        if (b > 0){
            //b = b*2;

        }
        fragColor = vec4(b*light_color*color_filter, 1.0); // Red for hit
        //fragColor = vec4(1, 0.0, 0.0, 1.0); // Red for hit
        //fragColor = vec4(abs(ray_dir),1.0);
    } else {
        vec2 Noisepos = -vec2(camera_dir.y,camera_dir.x);
        //float noiseValue = perlinNoise(Noisepos+uv);
        float noiseValue = perlinNoise(uv);
        fragColor = vec4(0.0, 0.0, 1.0, 1.0); // Blue for miss
        fragColor = vec4(vec3(noiseValue * 0.5 + 0.5), 1.0);

        fragColor = vec4(0,0,0,0);
    }
    normalColor = vec4(abs(ray_dir),1.0);
}
