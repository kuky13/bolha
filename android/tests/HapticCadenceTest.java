// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import static solutions.kuky.bolha.mobile.HapticCadence.Pulse.*;

public final class HapticCadenceTest {
    public static void main(String[] args) {
        HapticCadence cadence = new HapticCadence();
        expect(ANGER, cadence.frame(true, 1, 0));
        expect(NONE, cadence.frame(true, 1, 17));
        expect(NONE, cadence.frame(false, 0, 20));
        expect(NONE, cadence.frame(true, 0, 40));
        expect(NONE, cadence.frame(true, 0, 7000));
        expect(NONE, cadence.frame(false, 0, 7001));
        expect(ANGER, cadence.frame(true, 0, 7002));
        expect(IMPACT, cadence.frame(true, 2, 7250));
        expect(NONE, cadence.frame(true, 2, 7500));
        expect(IMPACT, cadence.frame(true, 3, 7501));
        expect(NONE, cadence.frame(false, 4, 7502));
        expect(NONE, cadence.frame(false, 4, 7700));
        expect(IMPACT, cadence.frame(false, 5, 7701));
    }

    private static void expect(HapticCadence.Pulse expected, HapticCadence.Pulse actual) {
        if (expected != actual) throw new AssertionError("Esperado: " + expected + ", obtido: " + actual);
    }
}
