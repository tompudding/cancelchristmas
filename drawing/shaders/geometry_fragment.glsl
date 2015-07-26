#version 130

uniform sampler2D tex;
uniform sampler2D normal_tex;
uniform sampler2D occlude_tex;
uniform sampler2D displace_tex;
uniform int using_textures;

in vec2 vs_displacement;
in vec2 vs_texcoord;
in vec2 vs_normal_coord;
in vec2 vs_occlude_coord;
in vec4 vs_colour;

out vec4 diffuse;
out vec4 normal;
out vec4 displacement;
out vec4 occlude;

void main()
{
    //displacement = mix(vs_position,vec3(1,1,1),0.99);
    if( 1 == using_textures ) {
        diffuse   = texture(tex, vs_texcoord)*vs_colour;
        vec3 normal_out = texture(normal_tex, vs_normal_coord).xyz;
        occlude = texture(occlude_tex, vs_occlude_coord);
        displacement = texture(displace_tex,vs_displacement);
        normal = vec4(normal_out,1);
        if(diffuse.a == 0.0 || normal.a == 0.0) {
            discard;
        }
    }
    else {
        diffuse = vs_colour;
        normal = vec4(0,0,0,1);
        occlude = vec4(0,0,0,0);
        displacement = vec4(0,0,0,0);
    }
}
