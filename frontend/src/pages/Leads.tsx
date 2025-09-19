import { motion } from "framer-motion";
import { useState } from "react";
import { 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Edit, 
  Phone, 
  MessageCircle,
  MoreHorizontal
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const mockLeads = [
  {
    id: 1,
    name: "Maria Silva",
    city: "São Paulo",
    whatsapp: "(11) 99999-9999",
    stage: "Qualified",
    status: "hot",
    assignedCloser: "João Santos",
    lastContact: "2024-01-15",
    nextAction: "Schedule call",
  },
  {
    id: 2,
    name: "Carlos Oliveira",
    city: "Rio de Janeiro",
    whatsapp: "(21) 98888-8888",
    stage: "Contacted",
    status: "warm",
    assignedCloser: "Ana Costa",
    lastContact: "2024-01-14",
    nextAction: "Send proposal",
  },
  {
    id: 3,
    name: "Fernanda Lima",
    city: "Belo Horizonte",
    whatsapp: "(31) 97777-7777",
    stage: "Proposed",
    status: "hot",
    assignedCloser: "Pedro Alves",
    lastContact: "2024-01-13",
    nextAction: "Follow up",
  },
  {
    id: 4,
    name: "Roberto Santos",
    city: "Brasília",
    whatsapp: "(61) 96666-6666",
    stage: "New",
    status: "cold",
    assignedCloser: "Lucia Mendes",
    lastContact: "2024-01-12",
    nextAction: "First contact",
  },
  {
    id: 5,
    name: "Julia Ferreira",
    city: "Curitiba",
    whatsapp: "(41) 95555-5555",
    stage: "Booked",
    status: "hot",
    assignedCloser: "João Santos",
    lastContact: "2024-01-11",
    nextAction: "Confirm appointment",
  },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case "hot":
      return "bg-hot text-white";
    case "warm":
      return "bg-warm text-white";
    case "cold":
      return "bg-cold text-white";
    default:
      return "bg-muted text-muted-foreground";
  }
};

const getStageColor = (stage: string) => {
  switch (stage) {
    case "New":
      return "bg-muted text-muted-foreground";
    case "Contacted":
      return "bg-blue-100 text-blue-800";
    case "Qualified":
      return "bg-primary-soft text-primary";
    case "Proposed":
      return "bg-accent-soft text-accent";
    case "Booked":
      return "bg-success-soft text-success";
    case "Confirmed":
      return "bg-green-100 text-green-800";
    default:
      return "bg-muted text-muted-foreground";
  }
};

export default function Leads() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");

  const filteredLeads = mockLeads.filter(lead => {
    const matchesSearch = lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lead.city.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || lead.status === statusFilter;
    const matchesStage = stageFilter === "all" || lead.stage === stageFilter;
    
    return matchesSearch && matchesStatus && matchesStage;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center"
      >
        <div>
          <h1 className="text-3xl font-bold text-foreground">Leads & CRM</h1>
          <p className="text-muted-foreground">
            Manage your leads and track conversion progress
          </p>
        </div>
        <Button className="rounded-2xl bg-primary hover:bg-primary-hover">
          <Plus className="h-4 w-4 mr-2" />
          New Lead
        </Button>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search leads by name or city..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 rounded-2xl border-border focus:ring-primary focus:border-primary"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-32 rounded-2xl border-border">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl">
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="hot">Hot</SelectItem>
                    <SelectItem value="warm">Warm</SelectItem>
                    <SelectItem value="cold">Cold</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select value={stageFilter} onValueChange={setStageFilter}>
                  <SelectTrigger className="w-32 rounded-2xl border-border">
                    <SelectValue placeholder="Stage" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl">
                    <SelectItem value="all">All Stages</SelectItem>
                    <SelectItem value="New">New</SelectItem>
                    <SelectItem value="Contacted">Contacted</SelectItem>
                    <SelectItem value="Qualified">Qualified</SelectItem>
                    <SelectItem value="Proposed">Proposed</SelectItem>
                    <SelectItem value="Booked">Booked</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Leads Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="rounded-2xl shadow-card border-border">
          <CardHeader>
            <CardTitle>Leads ({filteredLeads.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>WhatsApp</TableHead>
                    <TableHead>Stage</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Assigned Closer</TableHead>
                    <TableHead>Last Contact</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLeads.map((lead, index) => (
                    <motion.tr
                      key={lead.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + index * 0.05 }}
                      className="hover:bg-muted/50 transition-colors"
                    >
                      <TableCell className="font-medium">{lead.name}</TableCell>
                      <TableCell>{lead.city}</TableCell>
                      <TableCell>{lead.whatsapp}</TableCell>
                      <TableCell>
                        <Badge className={`rounded-full ${getStageColor(lead.stage)}`}>
                          {lead.stage}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={`rounded-full ${getStatusColor(lead.status)}`}>
                          {lead.status.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>{lead.assignedCloser}</TableCell>
                      <TableCell>{new Date(lead.lastContact).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                            <Phone className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                            <MessageCircle className="h-4 w-4" />
                          </Button>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg hover:bg-secondary">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="rounded-2xl" align="end">
                              <DropdownMenuItem className="rounded-xl">
                                <Edit className="h-4 w-4 mr-2" />
                                Edit Lead
                              </DropdownMenuItem>
                              <DropdownMenuItem className="rounded-xl">
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem className="rounded-xl">
                                Change Status
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
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