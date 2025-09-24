import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import { metricsService } from "@/services/metrics";

export default function Dashboard() {
  const { data: overview } = useQuery({
    queryKey: ['metrics', 'overview'],
    queryFn: metricsService.getOverview,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: telephonyMetrics } = useQuery({
    queryKey: ['metrics', 'telephony'],
    queryFn: metricsService.getTelephonyMetrics,
    refetchInterval: 30000,
  });

  const { data: whatsappMetrics } = useQuery({
    queryKey: ['metrics', 'whatsapp'],
    queryFn: metricsService.getWhatsAppMetrics,
    refetchInterval: 30000,
  });

  // Dynamic KPI data based on API response
  const kpiData = overview ? [
    {
      title: "Contact Rate",
      value: `${overview.funnel.contact_rate.toFixed(1)}%`,
      change: { value: "+5.2%", trend: "up" as const },
      icon: Phone,
    },
    {
      title: "Booking Rate",
      value: `${overview.funnel.booking_rate.toFixed(1)}%`,
      change: { value: "+2.1%", trend: "up" as const },
      icon: Calendar,
    },
    {
      title: "Show Rate",
      value: `${overview.funnel.show_rate.toFixed(1)}%`,
      change: { value: "-1.5%", trend: "down" as const },
      icon: CheckCircle2,
    },
    {
      title: "Avg Handle Time",
      value: "4.2min", // This would need to be calculated from call data
      change: { value: "-0.3min", trend: "up" as const },
      icon: Clock,
    },
  ] : [
    {
      title: "Contact Rate",
      value: "...",
      change: { value: "", trend: "up" as const },
      icon: Phone,
    },
    {
      title: "Booking Rate",
      value: "...",
      change: { value: "", trend: "up" as const },
      icon: Calendar,
    },
    {
      title: "Show Rate",
      value: "...",
      change: { value: "", trend: "down" as const },
      icon: CheckCircle2,
    },
    {
      title: "Avg Handle Time",
      value: "...",
      change: { value: "", trend: "up" as const },
      icon: Clock,
    },
  ];

  // Dynamic funnel data based on API response
  const funnelData = overview ? [
    {
      stage: "New Leads",
      count: overview.funnel.leads_new,
      percentage: 100,
      color: "bg-blue-500"
    },
    {
      stage: "Contacted",
      count: overview.funnel.leads_contacted,
      percentage: overview.funnel.leads_new > 0 ? (overview.funnel.leads_contacted / overview.funnel.leads_new) * 100 : 0,
      color: "bg-blue-600"
    },
    {
      stage: "Qualified",
      count: overview.funnel.leads_qualified,
      percentage: overview.funnel.leads_new > 0 ? (overview.funnel.leads_qualified / overview.funnel.leads_new) * 100 : 0,
      color: "bg-primary"
    },
    {
      stage: "Booked",
      count: overview.funnel.leads_booked,
      percentage: overview.funnel.leads_new > 0 ? (overview.funnel.leads_booked / overview.funnel.leads_new) * 100 : 0,
      color: "bg-success"
    },
    {
      stage: "Showed",
      count: overview.funnel.leads_showed,
      percentage: overview.funnel.leads_new > 0 ? (overview.funnel.leads_showed / overview.funnel.leads_new) * 100 : 0,
      color: "bg-green-600"
    },
  ] : [
    { stage: "New Leads", count: 0, percentage: 0, color: "bg-blue-500" },
    { stage: "Contacted", count: 0, percentage: 0, color: "bg-blue-600" },
    { stage: "Qualified", count: 0, percentage: 0, color: "bg-primary" },
    { stage: "Booked", count: 0, percentage: 0, color: "bg-success" },
    { stage: "Showed", count: 0, percentage: 0, color: "bg-green-600" },
  ];

  // Dynamic stats data based on API response
  const statsData = [
    {
      category: "Telephony",
      stats: telephonyMetrics ? [
        { label: "Calls Made", value: telephonyMetrics.totals.calls_initiated.toString() },
        { label: "Calls Answered", value: telephonyMetrics.totals.calls_answered.toString() },
        { label: "Answer Rate", value: `${telephonyMetrics.totals.answer_rate.toFixed(1)}%` },
        { label: "Total Cost", value: `$${telephonyMetrics.totals.total_cost_dollars.toFixed(2)}` },
      ] : [
        { label: "Calls Made", value: "..." },
        { label: "Calls Answered", value: "..." },
        { label: "Answer Rate", value: "..." },
        { label: "Total Cost", value: "..." },
      ],
    },
    {
      category: "WhatsApp",
      stats: whatsappMetrics ? [
        { label: "Messages Sent", value: whatsappMetrics.totals.messages_sent.toLocaleString() },
        { label: "Delivered", value: whatsappMetrics.totals.messages_delivered.toLocaleString() },
        { label: "Delivery Rate", value: `${whatsappMetrics.totals.delivery_rate.toFixed(1)}%` },
        { label: "Response Rate", value: `${whatsappMetrics.totals.response_rate.toFixed(1)}%` },
      ] : [
        { label: "Messages Sent", value: "..." },
        { label: "Delivered", value: "..." },
        { label: "Delivery Rate", value: "..." },
        { label: "Response Rate", value: "..." },
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
                      {item.count} ({item.percentage.toFixed(1)}%)
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