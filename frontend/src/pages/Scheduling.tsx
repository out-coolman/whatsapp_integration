import { motion } from "framer-motion";
import { useState } from "react";
import { 
  Calendar as CalendarIcon, 
  Plus, 
  Filter, 
  Clock,
  User,
  MapPin,
  Phone
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const mockAppointments = [
  {
    id: 1,
    patientName: "Maria Silva",
    professional: "Dr. João Santos",
    unit: "Clínica Centro",
    type: "Consulta",
    date: "2024-01-15",
    time: "09:00",
    duration: 30,
    status: "confirmed",
    phone: "(11) 99999-9999",
  },
  {
    id: 2,
    patientName: "Carlos Oliveira",
    professional: "Dr. Ana Costa",
    unit: "Clínica Norte",
    type: "Retorno",
    date: "2024-01-15",
    time: "10:30",
    duration: 20,
    status: "pending",
    phone: "(21) 98888-8888",
  },
  {
    id: 3,
    patientName: "Fernanda Lima",
    professional: "Dr. Pedro Alves",
    unit: "Clínica Sul",
    type: "Exame",
    date: "2024-01-15",
    time: "14:00",
    duration: 45,
    status: "confirmed",
    phone: "(31) 97777-7777",
  },
  {
    id: 4,
    patientName: "Roberto Santos",
    professional: "Dr. Lucia Mendes",
    unit: "Clínica Centro",
    type: "Primeira Consulta",
    date: "2024-01-16",
    time: "08:30",
    duration: 60,
    status: "rescheduled",
    phone: "(61) 96666-6666",
  },
  {
    id: 5,
    patientName: "Julia Ferreira",
    professional: "Dr. João Santos",
    unit: "Clínica Norte",
    type: "Consulta",
    date: "2024-01-16",
    time: "11:00",
    duration: 30,
    status: "confirmed",
    phone: "(41) 95555-5555",
  },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case "confirmed":
      return "bg-success-soft text-success";
    case "pending":
      return "bg-warning-soft text-warning";
    case "rescheduled":
      return "bg-blue-100 text-blue-800";
    case "cancelled":
      return "bg-destructive-soft text-destructive";
    default:
      return "bg-muted text-muted-foreground";
  }
};

export default function Scheduling() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [professionalFilter, setProfessionalFilter] = useState("all");
  const [unitFilter, setUnitFilter] = useState("all");

  const selectedDateString = selectedDate.toISOString().split('T')[0];
  const filteredAppointments = mockAppointments.filter(appointment => {
    const matchesDate = appointment.date === selectedDateString;
    const matchesProfessional = professionalFilter === "all" || appointment.professional === professionalFilter;
    const matchesUnit = unitFilter === "all" || appointment.unit === unitFilter;
    
    return matchesDate && matchesProfessional && matchesUnit;
  });

  const professionals = [...new Set(mockAppointments.map(apt => apt.professional))];
  const units = [...new Set(mockAppointments.map(apt => apt.unit))];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center"
      >
        <div>
          <h1 className="text-3xl font-bold text-foreground">Scheduling</h1>
          <p className="text-muted-foreground">
            Manage appointments and calendar from Ninsaúde
          </p>
        </div>
        <Button className="rounded-2xl bg-primary hover:bg-primary-hover">
          <Plus className="h-4 w-4 mr-2" />
          New Appointment
        </Button>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <Card className="rounded-2xl shadow-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <CalendarIcon className="h-5 w-5 text-primary" />
                <span>Calendar</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={(date) => date && setSelectedDate(date)}
                className="rounded-2xl pointer-events-auto"
              />
              
              {/* Filters */}
              <div className="space-y-4 mt-6">
                <div>
                  <label className="text-sm font-medium text-foreground mb-2 block">
                    Professional
                  </label>
                  <Select value={professionalFilter} onValueChange={setProfessionalFilter}>
                    <SelectTrigger className="rounded-2xl border-border">
                      <SelectValue placeholder="All Professionals" />
                    </SelectTrigger>
                    <SelectContent className="rounded-2xl">
                      <SelectItem value="all">All Professionals</SelectItem>
                      {professionals.map(prof => (
                        <SelectItem key={prof} value={prof}>{prof}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-foreground mb-2 block">
                    Unit
                  </label>
                  <Select value={unitFilter} onValueChange={setUnitFilter}>
                    <SelectTrigger className="rounded-2xl border-border">
                      <SelectValue placeholder="All Units" />
                    </SelectTrigger>
                    <SelectContent className="rounded-2xl">
                      <SelectItem value="all">All Units</SelectItem>
                      {units.map(unit => (
                        <SelectItem key={unit} value={unit}>{unit}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Appointments List */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card className="rounded-2xl shadow-card border-border">
            <CardHeader>
              <CardTitle>
                Appointments for {selectedDate.toLocaleDateString()}
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({filteredAppointments.length} appointments)
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredAppointments.length > 0 ? (
                  filteredAppointments.map((appointment, index) => (
                    <motion.div
                      key={appointment.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                      className="border border-border rounded-2xl p-4 hover:shadow-hover transition-all duration-300"
                    >
                      <div className="flex items-center justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-3">
                            <h3 className="font-semibold text-foreground">
                              {appointment.patientName}
                            </h3>
                            <Badge className={`rounded-full ${getStatusColor(appointment.status)}`}>
                              {appointment.status}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center space-x-2">
                              <Clock className="h-4 w-4" />
                              <span>{appointment.time} ({appointment.duration}min)</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <User className="h-4 w-4" />
                              <span>{appointment.professional}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <MapPin className="h-4 w-4" />
                              <span>{appointment.unit}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Phone className="h-4 w-4" />
                              <span>{appointment.phone}</span>
                            </div>
                          </div>
                          
                          <div className="text-sm">
                            <span className="font-medium text-foreground">Type: </span>
                            <span className="text-muted-foreground">{appointment.type}</span>
                          </div>
                        </div>
                        
                        <div className="flex flex-col space-y-2">
                          <Button variant="outline" size="sm" className="rounded-2xl border-border">
                            Reschedule
                          </Button>
                          {appointment.status === "confirmed" && (
                            <Button variant="outline" size="sm" className="rounded-2xl border-primary text-primary hover:bg-primary-soft">
                              Send Reminder
                            </Button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <CalendarIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                      No appointments scheduled for this date
                    </p>
                  </motion.div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}