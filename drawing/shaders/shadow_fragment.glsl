#version 130

uniform sampler2D colour_map;
uniform sampler2D position_map;
uniform sampler2D normal_map;
uniform sampler2D occlude_map;
uniform vec3 sb_dimensions;
uniform vec3 screen_dimensions;

uniform vec2 light_pos;
uniform vec2 light_dimensions;
out vec4 out_colour;

#define PI 3.14159

vec2 CalcTexCoord()
{
    return gl_FragCoord.xy / sb_dimensions.xy;
}


void main()
{
    float distance = 1.0;
    vec2 lp = light_pos/screen_dimensions.xy;
    vec4 occlude   = texture(occlude_map, CalcTexCoord());
    for(float y=0.0; y < 128; y += 1.0) {
        float theta = ((gl_FragCoord.x/sb_dimensions.x)*2.0)-1;
        float r = y/128;
        theta = PI*1.5 + theta*PI;

        vec2 coord = vec2(-r * sin(theta), -r * cos(theta));
        //coord.y *= 1.41;
        coord *= vec2(384,384)/screen_dimensions.xy;
        coord += lp;
        //coord = vec2(0.48,0.56);
        if(coord.x > 1 || coord.y > 1 || coord.x < 0 || coord.y < 0) {
            continue;
        }

        //sample the occlusion map
        vec4 data = texture(occlude_map, coord);
        //distance = data.r;
        if(data.r > 0.75) {
            distance = min(distance,r);
        }
    }
    //out_colour = mix(occlude,vec4(distance,distance,distance,1),0.5);
    out_colour = vec4(distance,distance,distance,1);
}
