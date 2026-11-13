// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.AppOpsManager;
import android.app.usage.UsageEvents;
import android.app.usage.UsageStatsManager;
import android.content.Context;
import android.os.Process;

/** Optional package-only context, gated by Android's explicit usage access. */
final class UsageContext {
    private final Context context;
    private long checked;
    private String packageName = "";

    UsageContext(Context context) { this.context = context; }

    static boolean permitted(Context context) {
        AppOpsManager manager = context.getSystemService(AppOpsManager.class);
        return manager != null && manager.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS,
                Process.myUid(),context.getPackageName()) == AppOpsManager.MODE_ALLOWED;
    }

    String activePackage() {
        if (!permitted(context)) {
            checked = 0;
            packageName = "";
            return packageName;
        }
        long now = System.currentTimeMillis();
        long begin = checked == 0 ? now - 24L*60*60*1000 : checked;
        UsageStatsManager manager = context.getSystemService(UsageStatsManager.class);
        if (manager == null) return "";
        try {
            UsageEvents events = manager.queryEvents(begin,now);
            UsageEvents.Event event = new UsageEvents.Event();
            while (events.hasNextEvent()) {
                events.getNextEvent(event);
                if (event.getEventType() == UsageEvents.Event.MOVE_TO_FOREGROUND)
                    packageName = event.getPackageName();
            }
            checked = now;
            return packageName;
        } catch (SecurityException unavailable) {
            packageName = "";
            checked = 0;
            return packageName;
        }
    }
}
