// SPDX-License-Identifier: GPL-3.0-or-later
// Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
package solutions.kuky.bolha.mobile;

import android.app.Activity;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

final class MobileUi {
    static final int BACKGROUND = Color.rgb(24,20,32);
    static final int SURFACE = Color.rgb(36,30,46);
    static final int TEXT = Color.rgb(246,239,255);
    static final int MUTED = Color.rgb(192,178,207);
    static final int GOLD = Color.rgb(255,211,100);
    static final int PURPLE = Color.rgb(172,137,209);

    static int dp(Context context, float value) {
        return Math.round(value * context.getResources().getDisplayMetrics().density);
    }

    static LinearLayout column(Context context) {
        LinearLayout layout = new LinearLayout(context);
        layout.setOrientation(LinearLayout.VERTICAL);
        return layout;
    }

    static LinearLayout row(Context context) {
        LinearLayout layout = new LinearLayout(context);
        layout.setOrientation(LinearLayout.HORIZONTAL);
        return layout;
    }

    static TextView text(Context context, String value, int size, int color) {
        TextView view = new TextView(context);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setLineSpacing(dp(context,3),1);
        return view;
    }

    static TextView title(Context context, String value) {
        TextView view = text(context,value,22,TEXT);
        view.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        view.setPadding(0,dp(context,6),0,dp(context,12));
        return view;
    }

    static GradientDrawable background(Context context, int color, int radius) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(color);
        shape.setCornerRadius(dp(context,radius));
        return shape;
    }

    static Button button(Context context, String label, Runnable action) {
        Button view = new Button(context);
        view.setText(label);
        view.setAllCaps(false);
        view.setTextSize(15);
        view.setTextColor(TEXT);
        view.setMinHeight(dp(context,52));
        view.setPadding(dp(context,14),dp(context,8),dp(context,14),dp(context,8));
        view.setBackgroundTintList(ColorStateList.valueOf(Color.rgb(63,49,79)));
        view.setOnClickListener(ignored -> action.run());
        return view;
    }

    static void addEqual(LinearLayout row, View view) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0,-2,1);
        params.setMargins(dp(row.getContext(),3),dp(row.getContext(),3),
                          dp(row.getContext(),3),dp(row.getContext(),3));
        row.addView(view,params);
    }

    static LinearLayout card(Context context, LinearLayout parent) {
        LinearLayout card = column(context);
        int padding = dp(context,16);
        card.setPadding(padding,padding,padding,padding);
        card.setBackground(background(context,SURFACE,18));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1,-2);
        params.setMargins(0,0,0,dp(context,12));
        parent.addView(card,params);
        return card;
    }

    static void applyWindow(Activity activity, View root) {
        root.setBackgroundColor(BACKGROUND);
        activity.getWindow().setStatusBarColor(BACKGROUND);
        activity.getWindow().setNavigationBarColor(BACKGROUND);
        if (Build.VERSION.SDK_INT >= 30) root.setOnApplyWindowInsetsListener((view,insets) -> {
            android.graphics.Insets bars = insets.getInsets(
                WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            view.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            return insets;
        });
    }

    private MobileUi() {}
}
