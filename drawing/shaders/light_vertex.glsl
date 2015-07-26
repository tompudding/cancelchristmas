#version 130

uniform vec3 screen_dimensions;
uniform vec2 translation;
uniform vec2 scale;

in vec3 vertex_data;

void main()
{
    gl_Position = vec4( (((vertex_data.x+translation.x)*2*scale.x)/screen_dimensions.x)-1,
                        (((vertex_data.y+translation.y)*2*scale.y)/screen_dimensions.y)-1,
                        -vertex_data.z/screen_dimensions.z,1.0 );
}
