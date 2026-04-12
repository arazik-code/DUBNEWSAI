import { Pressable, StyleSheet, Text, View } from "react-native";

import { Surface } from "./surface";

import { formatCurrency, formatPercent } from "@/lib/formatters";
import { useAppTheme } from "@/lib/theme";
import type { MobileMarketCard } from "@/lib/api/types";

type MarketCardProps = {
  item: MobileMarketCard;
  onPress?: () => void;
};

export function MarketCard({ item, onPress }: MarketCardProps) {
  const { colors } = useAppTheme();
  const positive = item.change_percent >= 0;

  return (
    <Pressable onPress={onPress} disabled={!onPress}>
      <Surface>
        <View style={styles.container}>
          <View style={styles.topRow}>
            <View style={styles.copy}>
              <Text style={[styles.symbol, { color: colors.text }]}>{item.symbol}</Text>
              <Text style={[styles.name, { color: colors.textMuted }]} numberOfLines={1}>
                {item.name}
              </Text>
            </View>
            <View
              style={[
                styles.changePill,
                {
                  backgroundColor: positive ? "rgba(49, 196, 141, 0.14)" : "rgba(248, 113, 113, 0.14)",
                },
              ]}
            >
              <Text style={{ color: positive ? colors.success : colors.danger, fontWeight: "700" }}>
                {formatPercent(item.change_percent)}
              </Text>
            </View>
          </View>
          <Text style={[styles.price, { color: colors.text }]}>{formatCurrency(item.price, item.currency)}</Text>
          <Text style={[styles.meta, { color: colors.textMuted }]}>
            {(item.exchange || item.market_type || "Market").toUpperCase()}
          </Text>
        </View>
      </Surface>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
  },
  copy: {
    flex: 1,
    gap: 4,
  },
  symbol: {
    fontSize: 17,
    fontWeight: "800",
  },
  name: {
    fontSize: 13,
  },
  price: {
    fontSize: 22,
    fontWeight: "800",
  },
  meta: {
    fontSize: 11,
    letterSpacing: 1.3,
    textTransform: "uppercase",
  },
  changePill: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 999,
    alignSelf: "flex-start",
  },
});
