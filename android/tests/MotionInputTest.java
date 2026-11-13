// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

public final class MotionInputTest {
    public static void main(String[] args) {
        DragMotion finger=new DragMotion(3);
        finger.start(100,150,50,80,0);
        finger.sample(62,96,16);
        close(112,finger.x());close(166,finger.y());
        expect(finger.moved());
        close(750,finger.vx());close(1000,finger.vy());
        // Native window motion never contributes to the raw finger delta.
        finger.sample(62,96,32);
        close(112,finger.x());close(166,finger.y());
        finger.sample(62,96,250);
        close(0,finger.vx());close(0,finger.vy());
        finger.start(48,64,10,10,300);
        finger.sample(11,10,320);
        expect(!finger.moved());close(0,finger.vx());
        for (int i=1;i<=40;i++) finger.sample(11+i*3,10,320+i*10);
        close(300,finger.vx());
        finger.sample(999,999,310);
        close(169,finger.x());

        ShakeMotion shake=new ShakeMotion();
        expect(!shake.sample(4,2,0,0,1));
        expect(!shake.sample(20,0,0,100,1));
        expect(shake.sample(-20,0,0,220,1));
        expect(!shake.sample(-20,0,0,340,1));
        expect(!shake.sample(20,0,0,460,1));
        expect(!shake.sample(20,0,0,1200,1));
        expect(shake.sample(-20,0,0,1320,1));
        shake.reset();
        expect(!shake.sample(20,0,0,0,.5f));
        expect(!shake.sample(-20,0,0,120,.5f));
        expect(!shake.sample(8,0,0,240,2));
        expect(shake.sample(-8,0,0,360,2));
        System.out.println("Movimento do dedo e detecção de chacoalhar aprovados.");
    }

    private static void close(float expected,float actual) {
        if (Math.abs(expected-actual)>.01f)
            throw new AssertionError("Esperado "+expected+", recebido "+actual);
    }

    private static void expect(boolean value) {
        if (!value) throw new AssertionError("Condição de gesto não satisfeita.");
    }
}
