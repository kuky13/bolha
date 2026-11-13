// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

/** Two separated acceleration peaks distinguish a shake from ordinary phone movement. */
final class ShakeMotion {
    private long peakAt = -1000, firedAt = -1000;
    private float previousX, previousY, previousZ;

    boolean sample(float x, float y, float z, long now, float sensitivity) {
        float threshold = 14f / Math.max(.5f, Math.min(2f, sensitivity));
        double length = Math.sqrt(x*x+y*y+z*z);
        if (length < threshold || now-peakAt < 90) return false;
        float dot = (float)((x*previousX+y*previousY+z*previousZ)/Math.max(1., length));
        boolean reversal = now-peakAt <= 650 && dot < .35f;
        peakAt = now;
        previousX = (float)(x/length);
        previousY = (float)(y/length);
        previousZ = (float)(z/length);
        if (reversal && now-firedAt >= 850) {
            firedAt = now;
            return true;
        }
        return false;
    }

    void reset() {
        peakAt = firedAt = -1000;
        previousX = previousY = previousZ = 0;
    }
}
