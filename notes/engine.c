
#include "datatypes/mapdata.h"
#include "datatypes/playerdata.h"
#include "render.h"
#include <math.h>
#include <graphx.h>
#include <string.h>
#include <tice.h>
#include <mymath.h>
#include "equates.h"
#include "gfx/trekvfx.h"
#include <compression.h>

char GUI_PrepareFrame(MapData_t *map, renderitem_t *renderbuffer, Position_t *playerpos){
    char i, count = 0;
    double val = 180/M_PI;
    unsigned long player_x = playerpos->coords.x;
    unsigned long player_y = playerpos->coords.y;
    unsigned long player_z = playerpos->coords.y;
    unsigned long item_x, item_y, item_z;
    long distance_x, distance_y, distance_z;
    unsigned long distance;
    memset(renderbuffer, 0, sizeof(renderitem_t) * 20);
    for(i=0; i<20; i++){
        MapData_t *item = &map[i];
        item_x = item->position.coords.x;
        item_y = item->position.coords.y;
        item_z = item->position.coords.z;
        distance_x = item_x - player_x;
        distance_y = item_y - player_y;
        distance_z = item_z - player_z;
        distance = (unsigned int)sqrt(r_GetDistance(distance_x, distance_y, distance_z));
        if(distance < RENDER_DISTANCE){
            unsigned char objectvect_xz = byteATan(distance_z, distance_x);
            unsigned char objectvect_y = byteATan(distance_y, distance_x);
            char diff_xz = compareAngles(objectvect_xz, playerpos->angles.xz);
            char diff_y = compareAngles(objectvect_y, playerpos->angles.y);
            if((abs(diff_xz) <= 32) && (abs(diff_y) <= 32)){
                int vcenter = vHeight>>1 + yStart;
                renderitem_t *render = &renderbuffer[count++];
                render->spriteid = item->entitytype-1;
                render->distance = (RENDER_DISTANCE - distance) * 100 / RENDER_DISTANCE;
                render->angle = diff_xz;
                diff_xz += 32;
                render->x = vWidth * diff_xz / 64 ;
                diff_y += 32;
                render->y = vHeight * diff_y / 64 + (2 * (RENDER_DISTANCE - distance));
            }
        }
    }
   // if(count>1) heapsort(renderbuffer, count);
    if(count>1) qsort(&renderbuffer, count, sizeof(renderitem_t), &compare_objects);
    return count;
}


void GUI_RenderFrame(gfx_sprite_t **sprites, buffers_t *buffers, renderitem_t *renderbuffer, char count){
    char i;
    for(i = 0; i < count; i++){
        renderitem_t *render = &renderbuffer[i];
        gfx_sprite_t* sprite = (gfx_sprite_t*)sprites[render->spriteid];
        gfx_sprite_t* rotated = buffers->rotated;
        gfx_sprite_t* scaled = buffers->scaled;
        char scale = render->distance;
        int width, height;
            //if(scale != -1){
        gfx_RotateSprite(sprite, rotated, render->angle);
        width = rotated->width * scale / 100;
        height = rotated->height * scale / 100;
        scaled->width = width;
        scaled->height = height;
        gfx_ScaleSprite(rotated, scaled);
        gfx_TransparentSprite(scaled, render->x - (scaled->width>>1), render->y);
    }
}

int compare_objects(const void *p, const void *q) {
    renderitem_t x = *(renderitem_t*)p;
    renderitem_t y = *(renderitem_t*)q;
    unsigned int dx = x.distance;
    unsigned int dy = y.distance;
    /* Avoid return x - y, which can cause undefined behaviour
     because of signed integer overflow. */
     
    if (dx < dy)
        return 1;  // Return -1 if you want ascending, 1 if you want descending order.
    else if (dx > dy)
        return -1;   // Return 1 if you want ascending, -1 if you want descending order.
    return 0;
}

void gfxinit_DecompressAll(gfx_sprite_t **array){
    char i;
    for(i = 0; i < trekvfx_num; i++){
        gfx_sprite_t* sprite = (gfx_sprite_t*)trekvfx[i];
        gfx_sprite_t *uncompressed = gfx_MallocSprite(64, 64);
        zx7_Decompress(uncompressed, sprite);
        array[i] = uncompressed;
    }
}

void gfxinit_FreeAll(gfx_sprite_t **array){
    char i;
    for(i = 0; i < trekvfx_num; i++){
        free(array[i]);
    }
}
