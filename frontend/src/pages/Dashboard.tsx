import { motion } from "framer-motion";
import { 
  TrendingUp, 
  Users, 
  Calendar, 
  Phone, 
  MessageCircle, 
  Clock,
  Target,
  CheckCircle2
} from "lucide-react";
import { StatsCard } from "@/components/ui/stats-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const kpiData = [
  {
    title: "Contact Rate",
    value: "78.5%",
    change: { value: "+5.2%", trend: "up" as const },
    icon: Phone,
  },
  {
    title: "Booking Rate",
    value: "34.2%",
    change: { value: "+2.1%", trend: "up" as const },
    icon: Calendar,
  },
  {
    title: "Show Rate",
    value: "89.3%",
    change: { value: "-1.5%", trend: "down" as const },
    icon: CheckCircle2,
  },
  {
    title: "Avg Handle Time",
    value: "4.2min",
    change: { value: "-0.3min", trend: "up" as const },
    icon: Clock,
  },
];

const funnelData = [
  { stage: "Leads", count: 1250, percentage: 100, color: "bg-blue-500" },
  { stage: "Contacted", count: 981, percentage: 78.5, color: "bg-blue-600" },
  { stage: "Qualified", count: 654, percentage: 52.3, color: "bg-primary" },
  { stage: "Proposed", count: 428, percentage: 34.2, color: "bg-accent" },
  { stage: "Booked", count: 312, percentage: 25.0, color: "bg-success" },
  { stage: "Confirmed", count: 279, percentage: 22.3, color: "bg-green-600" },
];

const statsData = [
  {
    category: "Telephony",
    stats: [
      { label: "Calls Made", value: "847" },
      { label: "Calls Answered", value: "623" },
      { label: "No Answer", value: "178" },
      { label: "Busy/Failed", value: "46" },
    ],
  },
  {
    category: "WhatsApp",
    stats: [
      { label: "Messages Sent", value: "1,234" },
      { label: "Delivered", value: "1,198" },
      { label: "Read", value: "891" },
      { label: "Avg Response Time", value: "2.4h" },
    ],
  },
  {
    category: "Operations",
    stats: [
      { label: "Human Handoffs", value: "23" },
      { label: "SLA Compliance", value: "94.2%" },
      { label: "Escalations", value: "12" },
      { label: "Resolution Rate", value: "87%" },
    ],
  },
];

export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground">
          Sales & Booking Orchestrator - Performance Overview
        </p>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiData.map((kpi, index) => (
          <motion.div
            key={kpi.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <StatsCard {...kpi} />
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Funnel Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="rounded-2xl shadow-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5 text-primary" />
                <span>Sales Funnel</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {funnelData.map((item, index) => (
                <motion.div
                  key={item.stage}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  className="space-y-2"
                >
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-foreground">
                      {item.stage}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                  <Progress 
                    value={item.percentage} 
                    className="h-3 rounded-full"
                  />
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* Stats Overview */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          {statsData.map((section, sectionIndex) => (
            <Card key={section.category} className="rounded-2xl shadow-card border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-foreground">
                  {section.category} Stats
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {section.stats.map((stat, index) => (
                    <motion.div
                      key={stat.label}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + sectionIndex * 0.1 + index * 0.05 }}
                      className="space-y-1"
                    >
                      <p className="text-xs text-muted-foreground">{stat.label}</p>
                      <p className="text-lg font-semibold text-foreground">{stat.value}</p>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </motion.div>
      </div>
    </div>
  );
}