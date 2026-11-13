// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

final class HapticCadence {
    enum Pulse { NONE, ANGER, IMPACT }

    private boolean angry;
    private long lastAnger = -6000;
    private long lastTap = -160;
    private double lastImpact;

    Pulse frame(boolean nextAngry, double impact, long now) {
        boolean angerPulse = nextAngry && !angry && now - lastAnger >= 6000;
        boolean impactPulse = impact > 0 && impact != lastImpact && now - lastTap >= 160;
        angry = nextAngry;
        lastImpact = impact;
        if (impactPulse) lastTap = now;
        if (angerPulse) {
            lastAnger = now;
            return Pulse.ANGER;
        }
        return impactPulse ? Pulse.IMPACT : Pulse.NONE;
    }
}
