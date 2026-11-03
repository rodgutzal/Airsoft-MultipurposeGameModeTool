#include "Ram.h"

uint8_t  gTeam;
bool     gArmed;
bool     gActionButton;
uint8_t  gKeyPressed;
uint32_t gSystemTickMs;

void InitRam(void)
{
    gTeam         = TEAM_RED;
    gArmed        = false;
    gActionButton = false;
    gKeyPressed   = 0xFF;
    gSystemTickMs = 0;
}
