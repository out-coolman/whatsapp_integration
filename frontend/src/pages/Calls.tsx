import { motion } from "framer-motion";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Phone,
  PhoneCall,
  PhoneMissed,
  Clock,
  Play,
  RefreshCw,
  UserCheck,
  AlertTriangle,
  Search,
  Filter
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { callsService, Call, CallStats } from "@/services/calls";

const getStatusIcon = (status: string) => {
  switch (status) {
    case "completed":
      return <PhoneCall className="h-4 w-4" />;
    case "no-answer":
      return <PhoneMissed className="h-4 w-4" />;
    case "busy":
      return <Phone className="h-4 w-4" />;
    case "escalated":
      return <AlertTriangle className="h-4 w-4" />;
    default:
      return <Phone className="h-4 w-4" />;
  }
};

export default function Calls() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Fetch calls data
  const { data: callsData, isLoading: callsLoading } = useQuery({
    queryKey: ['calls', statusFilter, searchTerm],
    queryFn: () => callsService.getCalls({
      status: statusFilter !== "all" ? statusFilter : undefined,
      search: searchTerm || undefined,
      limit: 100
    }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch call statistics
  const { data: callStats, isLoading: statsLoading } = useQuery({
    queryKey: ['calls', 'stats'],
    queryFn: () => callsService.getCallStats(),
    refetchInterval: 30000,
  });

  const calls = callsData || [];
  const stats = callStats || {
    total_calls: 0,
    answered_calls: 0,
    no_answer_calls: 0,
    escalated_calls: 0
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center"
      >
        <div>
          <h1 className="text-3xl font-bold text-foreground">Call Logs</h1>
          <p className="text-muted-foreground">
            VAPI voice call history and management
          </p>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        {[
          { title: "Total Calls", value: stats.total_calls.toString(), icon: Phone, color: "text-primary" },
          { title: "Answered", value: stats.answered_calls.toString(), icon: PhoneCall, color: "text-success" },
          { title: "No Answer", value: stats.no_answer_calls.toString(), icon: PhoneMissed, color: "text-warning" },
          { title: "Escalated", value: stats.escalated_calls.toString(), icon: AlertTriangle, color: "text-blue-600" },
        ].map((stat, index) => (
          <Card key={stat.title} className="rounded-2xl shadow-card border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold text-foreground">{statsLoading ? "..." : stat.value}</p>
                </div>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by lead name or phone..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 rounded-2xl border-border focus:ring-primary focus:border-primary"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40 rounded-2xl border-border">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl">
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="no_answer">No Answer</SelectItem>
                    <SelectItem value="busy">Busy</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="answered">Answered</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Calls Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardHeader>
            <CardTitle>Call History ({calls.length}) {callsLoading && "(Loading...)"}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Lead</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Outcome</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {calls.map((call, index) => (
                    <motion.tr
                      key={call.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 + index * 0.05 }}
                      className="hover:bg-muted/50 transition-colors"
                    >
                      <TableCell className="font-medium">
                        {call.lead_name || `Lead ${call.lead_id.slice(0, 8)}...`}
                      </TableCell>
                      <TableCell className="font-mono text-sm">{call.to_number}</TableCell>
                      <TableCell>
                        <Badge className={`rounded-full ${callsService.getStatusColor(call.status)} flex items-center space-x-1 w-fit`}>
                          {getStatusIcon(call.status)}
                          <span className="capitalize">{call.status.replace('_', ' ')}</span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>{callsService.formatDuration(call.duration_seconds)}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {new Date(call.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <span className={`text-sm ${call.outcome ? callsService.getOutcomeColor(call.outcome) : 'text-muted-foreground'}`}>
                          {call.outcome ? call.outcome.replace('_', ' ') : 'N/A'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm font-mono">
                          {callsService.formatCost(call.cost_cents)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {call.recording_url && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0 rounded-lg hover:bg-secondary"
                              onClick={() => callsService.playRecording(call.recording_url!)}
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                          {(call.status === "no_answer" || call.status === "busy") && (
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary text-primary">
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          )}
                          {call.ai_intent?.includes('handoff') && (
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary text-success">
                              <UserCheck className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}