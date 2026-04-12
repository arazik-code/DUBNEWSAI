import { Ionicons } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { Tabs } from "expo-router";
import { Platform, StyleSheet, Text, View } from "react-native";

import { useAppTheme } from "@/lib/theme";

function TabIcon({
  icon,
  color,
  focused,
  label,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  focused: boolean;
  label: string;
}) {
  return (
    <View style={styles.tabIcon}>
      <View style={[styles.iconChip, focused ? styles.iconChipActive : null]}>
        <Ionicons name={icon} size={20} color={color} />
      </View>
      <Text style={[styles.tabLabel, { color }]}>{label}</Text>
    </View>
  );
}

export default function TabsLayout() {
  const { colors, isDark } = useAppTheme();

  return (
    <Tabs
      screenListeners={{
        tabPress: () => {
          Haptics.selectionAsync().catch(() => undefined);
        },
      }}
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: false,
        sceneStyle: {
          backgroundColor: "transparent",
        },
        tabBarStyle: {
          position: "absolute",
          height: 88,
          paddingBottom: Platform.OS === "ios" ? 24 : 14,
          paddingTop: 10,
          borderTopWidth: 0,
          backgroundColor: "transparent",
          elevation: 0,
        },
        tabBarBackground: () => (
          <BlurView
            intensity={isDark ? 60 : 80}
            tint={isDark ? "dark" : "light"}
            style={[
              StyleSheet.absoluteFill,
              {
                overflow: "hidden",
                borderTopLeftRadius: 28,
                borderTopRightRadius: 28,
                borderColor: colors.border,
                borderWidth: 1,
              },
            ]}
          />
        ),
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.textMuted,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <TabIcon icon="sparkles" color={color} focused={focused} label="Home" />
          ),
        }}
      />
      <Tabs.Screen
        name="news"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <TabIcon icon="newspaper" color={color} focused={focused} label="News" />
          ),
        }}
      />
      <Tabs.Screen
        name="market"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <TabIcon icon="analytics" color={color} focused={focused} label="Market" />
          ),
        }}
      />
      <Tabs.Screen
        name="workspace"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <TabIcon icon="grid" color={color} focused={focused} label="Workspace" />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <TabIcon icon="person-circle" color={color} focused={focused} label="Profile" />
          ),
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabIcon: {
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  iconChip: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  iconChipActive: {
    backgroundColor: "rgba(255,255,255,0.08)",
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: "700",
  },
});
