// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

/** Tracks a finger in screen coordinates while its overlay window moves underneath it. */
final class DragMotion {
    private static final int SAMPLES = 16;
    private final float[] xs = new float[SAMPLES], ys = new float[SAMPLES];
    private final long[] times = new long[SAMPLES];
    private final float slop;
    private int count;
    private float pointerX, pointerY, centerX, centerY;
    private boolean moved;

    DragMotion(float slop) { this.slop = slop; }

    void start(float objectX, float objectY, float rawX, float rawY, long time) {
        centerX = objectX;
        centerY = objectY;
        pointerX = rawX;
        pointerY = rawY;
        count = 0;
        moved = false;
        sample(rawX, rawY, time);
    }

    void sample(float rawX, float rawY, long time) {
        if (count > 0 && time < times[(count-1)%SAMPLES]) return;
        int index = count%SAMPLES;
        xs[index] = rawX;
        ys[index] = rawY;
        times[index] = time;
        count++;
        moved |= Math.hypot(rawX-pointerX, rawY-pointerY) > slop;
    }

    float x() { return centerX + xs[(count-1)%SAMPLES] - pointerX; }
    float y() { return centerY + ys[(count-1)%SAMPLES] - pointerY; }
    boolean moved() { return moved; }
    float vx() { return velocity(xs); }
    float vy() { return velocity(ys); }

    private float velocity(float[] values) {
        if (!moved || count < 2) return 0;
        int last = (count-1)%SAMPLES;
        int first = count-1;
        while (first > Math.max(0, count-SAMPLES) && times[last]-times[(first-1)%SAMPLES] <= 100) first--;
        long elapsed = times[last]-times[first%SAMPLES];
        if (elapsed < 8) return 0;
        float velocity = (values[last]-values[first%SAMPLES])*1000f/elapsed;
        return Math.max(-1450f, Math.min(1450f, velocity));
    }
}
