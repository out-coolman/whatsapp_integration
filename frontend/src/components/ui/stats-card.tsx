import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: {
    value: string;
    trend: "up" | "down" | "neutral";
  };
  icon: LucideIcon;
  className?: string;
}

export function StatsCard({ title, value, change, icon: Icon, className }: StatsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card className={cn("border-border shadow-card hover:shadow-hover transition-all duration-300 rounded-2xl", className)}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <div className="space-y-1">
                <p className="text-2xl font-bold text-foreground">{value}</p>
                {change && (
                  <div className="flex items-center space-x-1">
                    <span
                      className={cn(
                        "text-xs font-medium",
                        change.trend === "up" && "text-success",
                        change.trend === "down" && "text-destructive",
                        change.trend === "neutral" && "text-muted-foreground"
                      )}
                    >
                      {change.trend === "up" && "↗"}
                      {change.trend === "down" && "↘"}
                      {change.value}
                    </span>
                    <span className="text-xs text-muted-foreground">vs last month</span>
                  </div>
                )}
              </div>
            </div>
            <div className="bg-primary-soft p-3 rounded-2xl">
              <Icon className="h-6 w-6 text-primary" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}