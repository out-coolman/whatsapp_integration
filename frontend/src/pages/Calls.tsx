import { motion } from "framer-motion";
import { useState } from "react";
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

const mockCalls = [
  {
    id: 1,
    leadName: "Maria Silva",
    phone: "(11) 99999-9999",
    status: "completed",
    duration: "4:32",
    timestamp: "2024-01-15 09:15",
    agent: "João Santos",
    outcome: "Interested - Scheduled",
    transcription: "Call transcript available",
    hasRecording: true,
  },
  {
    id: 2,
    leadName: "Carlos Oliveira",
    phone: "(21) 98888-8888",
    status: "no-answer",
    duration: "0:00",
    timestamp: "2024-01-15 08:45",
    agent: "Ana Costa",
    outcome: "No Answer",
    transcription: null,
    hasRecording: false,
  },
  {
    id: 3,
    leadName: "Fernanda Lima",
    phone: "(31) 97777-7777",
    status: "completed",
    duration: "7:18",
    timestamp: "2024-01-15 08:30",
    agent: "Pedro Alves",
    outcome: "Not Interested",
    transcription: "Call transcript available",
    hasRecording: true,
  },
  {
    id: 4,
    leadName: "Roberto Santos",
    phone: "(61) 96666-6666",
    status: "busy",
    duration: "0:15",
    timestamp: "2024-01-15 08:00",
    agent: "Lucia Mendes",
    outcome: "Busy Signal",
    transcription: null,
    hasRecording: false,
  },
  {
    id: 5,
    leadName: "Julia Ferreira",
    phone: "(41) 95555-5555",
    status: "escalated",
    duration: "12:45",
    timestamp: "2024-01-14 16:30",
    agent: "João Santos",
    outcome: "Escalated to Human",
    transcription: "Call transcript available",
    hasRecording: true,
  },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case "completed":
      return "bg-success-soft text-success";
    case "no-answer":
      return "bg-warning-soft text-warning";
    case "busy":
      return "bg-muted text-muted-foreground";
    case "failed":
      return "bg-destructive-soft text-destructive";
    case "escalated":
      return "bg-blue-100 text-blue-800";
    default:
      return "bg-muted text-muted-foreground";
  }
};

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
  const [agentFilter, setAgentFilter] = useState("all");

  const filteredCalls = mockCalls.filter(call => {
    const matchesSearch = call.leadName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.phone.includes(searchTerm);
    const matchesStatus = statusFilter === "all" || call.status === statusFilter;
    const matchesAgent = agentFilter === "all" || call.agent === agentFilter;
    
    return matchesSearch && matchesStatus && matchesAgent;
  });

  const agents = [...new Set(mockCalls.map(call => call.agent))];

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
          { title: "Total Calls", value: "847", icon: Phone, color: "text-primary" },
          { title: "Answered", value: "623", icon: PhoneCall, color: "text-success" },
          { title: "No Answer", value: "178", icon: PhoneMissed, color: "text-warning" },
          { title: "Escalated", value: "23", icon: AlertTriangle, color: "text-blue-600" },
        ].map((stat, index) => (
          <Card key={stat.title} className="rounded-2xl shadow-card border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold text-foreground">{stat.value}</p>
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
                    <SelectItem value="no-answer">No Answer</SelectItem>
                    <SelectItem value="busy">Busy</SelectItem>
                    <SelectItem value="escalated">Escalated</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={agentFilter} onValueChange={setAgentFilter}>
                  <SelectTrigger className="w-40 rounded-2xl border-border">
                    <SelectValue placeholder="Agent" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl">
                    <SelectItem value="all">All Agents</SelectItem>
                    {agents.map(agent => (
                      <SelectItem key={agent} value={agent}>{agent}</SelectItem>
                    ))}
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
            <CardTitle>Call History ({filteredCalls.length})</CardTitle>
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
                    <TableHead>Agent</TableHead>
                    <TableHead>Outcome</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCalls.map((call, index) => (
                    <motion.tr
                      key={call.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.4 + index * 0.05 }}
                      className="hover:bg-muted/50 transition-colors"
                    >
                      <TableCell className="font-medium">{call.leadName}</TableCell>
                      <TableCell className="font-mono text-sm">{call.phone}</TableCell>
                      <TableCell>
                        <Badge className={`rounded-full ${getStatusColor(call.status)} flex items-center space-x-1 w-fit`}>
                          {getStatusIcon(call.status)}
                          <span className="capitalize">{call.status.replace('-', ' ')}</span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>{call.duration}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {new Date(call.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>{call.agent}</TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">{call.outcome}</span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {call.hasRecording && (
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                          {call.status === "no-answer" || call.status === "busy" ? (
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary text-primary">
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          ) : null}
                          {call.status === "escalated" && (
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