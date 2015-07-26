#version 130

uniform sampler2D colour_map;
uniform sampler2D displacement_map;
uniform sampler2D normal_map;
uniform sampler2D occlude_map;
uniform sampler2D shadow_map;
uniform vec3 screen_dimensions;
uniform vec3 light_pos;
uniform int light_type;
uniform int shadow_index;
uniform vec3 ambient_colour;
uniform vec3 directional_light_dir;
uniform vec3 light_colour;
uniform float cone_dir;
uniform float cone_width;
uniform float ambient_attenuation;
uniform float light_radius;
uniform float light_intensity;
uniform vec2 translation;
uniform vec2 scale;
#define NUM_VALUES 4
float values[NUM_VALUES] = float[](0.05,0.09,0.12,0.15);

out vec4 out_colour;

#define PI 3.14159

vec2 CalcTexCoord()
{
    return gl_FragCoord.xy / screen_dimensions.xy;
}

//sample from the 1D distance map
float sample(vec2 coord, float r) {
    return step(r, texture(shadow_map, coord).r*384);
}

void main()
{
    vec2 tex_coord = CalcTexCoord();
    vec4 displacement = texture(displacement_map, tex_coord);
    vec4 occlude   = texture(occlude_map, tex_coord);
    vec4 colour    = texture(colour_map, tex_coord);
    vec4 shadow    = texture(shadow_map, tex_coord);
    vec3 normal    = normalize((texture(normal_map, tex_coord).xyz*2-vec3(1,1,1)));
    vec3 current_pos = (displacement.xyz-vec3(0.5,0.5,0.5))*256*3;
    current_pos += vec3(gl_FragCoord.xy,0);
    if(1 == light_type) {
        //1 is a uniform box of colour, e.g ambient
        //vec3 light_dir = normalize(-vec3(1,3,-1));
        vec3 light_dir = normalize(-directional_light_dir);
        vec3 diffuse = ambient_colour + (light_colour*max(dot(light_dir,normal),0.0));

        //Not using lighting right now so just output the colour

        //out_colour = vec4(colour.rgb*diffuse,0.1);
        //out_colour = mix(out_colour,displacement,1);
        out_colour = colour;
        //out_colour = vec4(normal.xyz,1);
        //out_colour = shadow;
    }
    else if(2 == light_type){
        //this is one for testing that follows the mouse
        vec2 adjust_xy = light_pos.xy-current_pos.xy;
        float theta = atan(-adjust_xy.y,-adjust_xy.x);
        float theta_diff = theta - cone_dir;
        float r = length(adjust_xy)*0.95;
        float coord = (PI-theta) / (2.0*PI);
        float jim = (shadow_index*3)/256.0;
        vec2 tc = vec2(coord,jim);
        float centre = sample(tc,r);
        float blur = 0.003;//(1/256.)*smoothstep(0.,1.,r);
        float sum = centre * 0.16;
        float falloff = 0.0;
        int i;
        if(theta_diff > PI) {
            theta_diff -= 2*PI;
        }
        if(theta_diff < -PI) {
            theta_diff += 2*PI;
        }
        if(abs(theta_diff) > cone_width) {
            discard;
        }
        if(abs(theta_diff) > cone_width-0.2) {
            falloff = (abs(theta_diff)-(cone_width-0.2))/0.2;
            falloff *= falloff;
        }
        for(i=0;i<NUM_VALUES;i++) {
            sum += sample(vec2(tc.x - (NUM_VALUES-i)*blur, tc.y), r) * values[i];
            sum += sample(vec2(tc.x - (i+1)*blur, tc.y), r) * values[NUM_VALUES-1-i];
        }

        //adjust_xy.y *= 1.41;
        //todo: use a height map to get the z coord
        vec3 light_dir = normalize(light_pos-current_pos);
        vec3 diffuse = light_colour*max(dot(light_dir,normal),0.0);
        float distance = min(length(adjust_xy)/light_radius,1);
        vec3 intensity = diffuse*(1-distance*distance)*(1-ambient_attenuation)*(1-falloff);
        //out_colour = mix(vec4(0,0,0,1),colour,value);
        out_colour = vec4(colour.rgb*intensity*sum,1);
        //out_colour.a *= centre;
    }
    else if(3 == light_type){
        vec3 world_light_pos = vec3( (light_pos.x+translation.x)*scale.x,
                                     (light_pos.y+translation.y)*scale.y,
                                     light_pos.z );
        vec2 adjust_xy = world_light_pos.xy-current_pos.xy;
        //adjust_xy.y *= 1.41;
        //todo: use a height map to get the z coord
        vec3 light_dir = normalize(world_light_pos-current_pos);
        vec3 diffuse = light_colour*max(dot(light_dir,normal),0.0);
        float distance = min(length(adjust_xy)/light_radius,1);
        vec3 intensity = diffuse*(1-distance*distance)*(1-ambient_attenuation);
        //out_colour = mix(vec4(0,0,0,1),colour,value);
        out_colour = vec4(colour.rgb*intensity*light_intensity,1);
    }
    else if(4 == light_type){
        //This is for the cone lights
        vec3 world_light_pos = vec3( (light_pos.x+translation.x)*scale.x,
                                     (light_pos.y+translation.y)*scale.y,
                                     light_pos.z );
        vec2 adjust_xy = world_light_pos.xy-current_pos.xy;
        float theta = atan(-adjust_xy.y,-adjust_xy.x);
        float theta_diff = theta - cone_dir;
        float r = length(adjust_xy)*0.95;
        float coord = (PI-theta) / (2.0*PI);
        vec2 tc = vec2(coord,shadow_index*3.0/256.0);
        float centre = sample(tc,r);
        float blur = 0.003;//(1/256.)*smoothstep(0.,1.,r);
        float sum = centre * 0.16;
        int i;
        float falloff = 0.0;
        if(theta_diff > PI) {
            theta_diff -= 2*PI;
        }
        if(theta_diff < -PI) {
            theta_diff += 2*PI;
        }
        if(abs(theta_diff) > cone_width) {
            discard;
        }
        if(abs(theta_diff) > cone_width-0.2) {
            falloff = (abs(theta_diff)-(cone_width-0.2))/0.2;
            falloff *= falloff;
        }
         for(i=0;i<NUM_VALUES;i++) {
            sum += sample(vec2(tc.x - (NUM_VALUES-i)*blur, tc.y), r) * values[i];
            sum += sample(vec2(tc.x - (i+1)*blur, tc.y), r) * values[NUM_VALUES-1-i];
        }

        //adjust_xy.y *= 1.41;
        //todo: use a height map to get the z coord
        vec3 light_dir = normalize(world_light_pos-current_pos);
        vec3 diffuse = light_colour*max(dot(light_dir,normal),0.0);
        float distance = min(length(adjust_xy)/400.0,1);
        vec3 intensity = diffuse*(1-distance*distance)*(1-ambient_attenuation)*(1-falloff);
        //out_colour = mix(vec4(0,0,0,1),colour,value);

        out_colour = vec4(colour.rgb*intensity,1);
    }

    //out_colour = mix(out_colour,occlude,0.1);
}
