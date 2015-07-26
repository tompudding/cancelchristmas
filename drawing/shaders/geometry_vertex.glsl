#version 130

uniform vec3 screen_dimensions;
uniform vec2 translation;
uniform vec2 scale;

in vec3 vertex_data;
in vec2 tc_data;
in vec2 normal_data;
in vec2 occlude_data;
in vec2 displace_data;
in vec4 colour_data;

out vec2 vs_displacement;
out vec2 vs_texcoord;
out vec2 vs_normal_coord;
out vec2 vs_occlude_coord;
out vec4 vs_colour;

void main()
{
    gl_Position = vec4( (((vertex_data.x+translation.x)*2*scale.x)/screen_dimensions.x)-1,
                        (((vertex_data.y+translation.y)*2*scale.y)/screen_dimensions.y)-1,
                        -vertex_data.z/screen_dimensions.z,1.0 );

    vs_displacement  = displace_data;
    vs_texcoord      = tc_data;
    vs_colour        = colour_data;
    vs_normal_coord  = normal_data;
    vs_occlude_coord = occlude_data;
}
